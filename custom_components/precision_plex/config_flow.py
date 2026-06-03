"""Config flow for Precision Plex read-only monitor.

Precision Plex BLE bonding config flow based on v2.6.33, promoted for v3.0.0.

v3.0.0 pairing-flow behavior:
- Registers a temporary BlueZ NoInputNoOutput pairing agent before pairing.
- Removes any stale BlueZ device object for the selected address before trying.
- Uses BleakClient(pair=True) while the agent is registered.
- Sends the existing v2.6.33 app init payload after a successful paired connect.

Why:
The iOS trace shows normal BLE SMP pairing after an Insufficient Authentication
response. The Home Assistant logs show BlueZ reaches the correct peripheral but
fails with org.bluez.Error.AuthenticationFailed. A missing/default-unavailable
BlueZ agent is a common cause for Just Works pairing failures in headless setups.
"""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS

from .const import (
    DEFAULT_TARGET_ADDRESS,
    DOMAIN,
    PAIRING_CHARACTERISTIC_UUID,
    PAIRING_INIT_PAYLOAD,
    TARGET_SERVICE_UUID,
)

_LOGGER = logging.getLogger(__name__)

CONF_PAIRING_MODE_CONFIRMED = "pairing_mode_confirmed"

CONNECT_TIMEOUT = 45.0
GATT_TIMEOUT = 10.0

BLUEZ_SERVICE = "org.bluez"
BLUEZ_AGENT_PATH = "/com/precision_plex/pairing_agent"


class PrecisionPlexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Precision Plex."""

    VERSION = 3

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        service_infos = bluetooth.async_discovered_service_info(self.hass)

        devices = {}
        for info in service_infos:
            service_uuids = [uuid.lower() for uuid in info.service_uuids or []]
            if TARGET_SERVICE_UUID.lower() in service_uuids or (
                info.name and info.name.lower().startswith("precision")
            ):
                devices[info.address] = (
                    f"{info.name} ({info.address})" if info.name else info.address
                )

        if not devices:
            devices[DEFAULT_TARGET_ADDRESS] = f"Precision Plex {DEFAULT_TARGET_ADDRESS}"

        if user_input is not None:
            self._address = user_input[CONF_ADDRESS]
            self._title = devices.get(self._address, f"Precision Plex {self._address}")
            return await self.async_step_pair()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ADDRESS,
                        default=next(iter(devices)),
                    ): vol.In(devices)
                }
            ),
            errors={},
        )

    async def async_step_pair(self, user_input=None):
        """Prompt for Precision Plex Pair with Mobile mode and bond."""
        errors = {}

        if user_input is not None:
            if not user_input.get(CONF_PAIRING_MODE_CONFIRMED):
                errors["base"] = "pairing_mode_required"
            else:
                address = getattr(self, "_address", None)
                title = getattr(self, "_title", None)

                if address is None:
                    return self.async_abort(reason="unknown")

                try:
                    await self._async_pair_and_prime(address)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning(
                        "Precision Plex BLE pairing/bonding failed for %s: %r",
                        address,
                        err,
                        exc_info=True,
                    )
                    errors["base"] = "pairing_failed"
                else:
                    await self.async_set_unique_id(address)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=title or f"Precision Plex {address}",
                        data={CONF_ADDRESS: address},
                    )

        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PAIRING_MODE_CONFIRMED, default=False): bool,
                }
            ),
            errors=errors,
            description_placeholders={
                "address": getattr(self, "_address", "unknown"),
            },
        )

    async def _async_pair_and_prime(self, address):
        """Register a BlueZ agent, pair during connect, then send app init."""
        from bleak import BleakClient, BleakError  # pylint: disable=import-outside-toplevel

        agent = BlueZPairingAgent(address)

        await agent.async_register()
        try:
            # Clear stale failed/partial BlueZ device records before the new
            # Pair with Mobile attempt.
            await agent.async_remove_device_if_present(address)

            ble_device = bluetooth.async_ble_device_from_address(
                self.hass,
                address,
                connectable=True,
            )
            if ble_device is None:
                raise BleakError(
                    f"Precision Plex device {address} is not visible to Home Assistant "
                    "Bluetooth. Put the console into Pair with Mobile mode, wait for "
                    "it to advertise, then try again."
                )

            _LOGGER.info(
                "Precision Plex setup connecting to %s with pair=True and BlueZ agent",
                address,
            )

            client = BleakClient(
                ble_device,
                timeout=CONNECT_TIMEOUT,
                pair=True,
            )

            try:
                await client.connect()

                if not client.is_connected:
                    raise BleakError(f"Failed to connect to Precision Plex {address}")

                _LOGGER.info(
                    "Precision Plex setup connected/paired to %s with BlueZ agent",
                    address,
                )

                await asyncio.sleep(1.0)

                pairing_char = client.services.get_characteristic(
                    PAIRING_CHARACTERISTIC_UUID
                )
                if pairing_char is None:
                    available = []
                    for service in client.services:
                        for char in service.characteristics:
                            available.append(char.uuid)
                    raise BleakError(
                        "Precision Plex app init characteristic "
                        f"{PAIRING_CHARACTERISTIC_UUID} not found after pairing. "
                        f"Available characteristics: {available}"
                    )

                _LOGGER.info(
                    "Precision Plex setup writing app init payload %s to %s",
                    PAIRING_INIT_PAYLOAD.hex(" "),
                    PAIRING_CHARACTERISTIC_UUID,
                )
                await asyncio.wait_for(
                    client.write_gatt_char(
                        pairing_char,
                        PAIRING_INIT_PAYLOAD,
                        response=False,
                    ),
                    timeout=GATT_TIMEOUT,
                )

                await asyncio.sleep(0.5)

                _LOGGER.info(
                    "Precision Plex setup pairing/bonding complete for %s",
                    address,
                )

            finally:
                if client.is_connected:
                    try:
                        await client.disconnect()
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug(
                            "Precision Plex setup disconnect failed for %s: %r",
                            address,
                            err,
                        )
        finally:
            await agent.async_unregister()


class BlueZPairingAgent:
    """Temporary BlueZ NoInputNoOutput pairing agent."""

    def __init__(self, address):
        """Initialize the agent wrapper."""
        self.address = address.upper()
        self.bus = None
        self.agent_interface = None
        self.agent_manager = None
        self.object_manager = None
        self.exported = False
        self.registered = False

    async def async_register(self):
        """Register this object as a temporary BlueZ pairing agent."""
        from dbus_fast import BusType  # pylint: disable=import-outside-toplevel
        from dbus_fast.aio import MessageBus  # pylint: disable=import-outside-toplevel
        from dbus_fast.service import (  # pylint: disable=import-outside-toplevel
            ServiceInterface,
            method,
        )

        target_address = self.address

        class AgentInterface(ServiceInterface):
            """BlueZ Agent1 implementation."""

            def __init__(self):
                super().__init__("org.bluez.Agent1")

            @method()
            def Release(self):
                _LOGGER.debug("Precision Plex BlueZ agent Release")

            @method()
            def RequestPinCode(self, device: "o") -> "s":
                _LOGGER.info(
                    "Precision Plex BlueZ agent RequestPinCode for %s", device
                )
                return "000000"

            @method()
            def DisplayPinCode(self, device: "o", pincode: "s"):
                _LOGGER.info(
                    "Precision Plex BlueZ agent DisplayPinCode for %s: %s",
                    device,
                    pincode,
                )

            @method()
            def RequestPasskey(self, device: "o") -> "u":
                _LOGGER.info(
                    "Precision Plex BlueZ agent RequestPasskey for %s; returning 0",
                    device,
                )
                return 0

            @method()
            def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
                _LOGGER.info(
                    "Precision Plex BlueZ agent DisplayPasskey for %s: %06d entered=%s",
                    device,
                    passkey,
                    entered,
                )

            @method()
            def RequestConfirmation(self, device: "o", passkey: "u"):
                _LOGGER.info(
                    "Precision Plex BlueZ agent auto-confirming passkey %06d for %s",
                    passkey,
                    device,
                )

            @method()
            def RequestAuthorization(self, device: "o"):
                _LOGGER.info(
                    "Precision Plex BlueZ agent authorizing pairing for %s", device
                )

            @method()
            def AuthorizeService(self, device: "o", uuid: "s"):
                _LOGGER.info(
                    "Precision Plex BlueZ agent authorizing service %s for %s",
                    uuid,
                    device,
                )

            @method()
            def Cancel(self):
                _LOGGER.info(
                    "Precision Plex BlueZ agent pairing request was canceled for %s",
                    target_address,
                )

        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        self.agent_interface = AgentInterface()
        self.bus.export(BLUEZ_AGENT_PATH, self.agent_interface)
        self.exported = True

        introspection = await self.bus.introspect(BLUEZ_SERVICE, "/org/bluez")
        bluez_obj = self.bus.get_proxy_object(BLUEZ_SERVICE, "/org/bluez", introspection)
        self.agent_manager = bluez_obj.get_interface("org.bluez.AgentManager1")

        await self.agent_manager.call_register_agent(
            BLUEZ_AGENT_PATH,
            "NoInputNoOutput",
        )
        self.registered = True
        _LOGGER.info("Precision Plex registered temporary BlueZ NoInputNoOutput agent")

        try:
            await self.agent_manager.call_request_default_agent(BLUEZ_AGENT_PATH)
            _LOGGER.info("Precision Plex BlueZ agent became default agent")
        except Exception as err:  # noqa: BLE001
            # Another process may already have default-agent ownership. Still
            # keep our registered agent; BlueZ can call it for this pair request.
            _LOGGER.info(
                "Precision Plex could not make BlueZ agent default; continuing: %r",
                err,
            )

        introspection = await self.bus.introspect(BLUEZ_SERVICE, "/")
        root_obj = self.bus.get_proxy_object(BLUEZ_SERVICE, "/", introspection)
        self.object_manager = root_obj.get_interface("org.freedesktop.DBus.ObjectManager")

    async def async_remove_device_if_present(self, address):
        """Remove a stale BlueZ device object for this address if present."""
        if self.object_manager is None or self.bus is None:
            return

        address = address.upper()
        objects = await self.object_manager.call_get_managed_objects()

        adapter_path = None
        device_path = None

        for path, interfaces in objects.items():
            if "org.bluez.Adapter1" in interfaces and adapter_path is None:
                adapter_path = path

            device = interfaces.get("org.bluez.Device1")
            if not device:
                continue

            props_address = str(device.get("Address", "")).upper()
            if props_address == address:
                device_path = path
                parent = path.rsplit("/", 1)[0]
                adapter_path = parent
                break

        if adapter_path is None or device_path is None:
            _LOGGER.info(
                "Precision Plex no stale BlueZ device object found for %s", address
            )
            return

        _LOGGER.info(
            "Precision Plex removing stale BlueZ device object %s for %s",
            device_path,
            address,
        )

        introspection = await self.bus.introspect(BLUEZ_SERVICE, adapter_path)
        adapter_obj = self.bus.get_proxy_object(BLUEZ_SERVICE, adapter_path, introspection)
        adapter = adapter_obj.get_interface("org.bluez.Adapter1")

        try:
            await adapter.call_remove_device(device_path)
        except Exception as err:  # noqa: BLE001
            _LOGGER.info(
                "Precision Plex failed to remove stale BlueZ device %s: %r",
                device_path,
                err,
            )

        await asyncio.sleep(1.0)

    async def async_unregister(self):
        """Unregister the temporary BlueZ pairing agent."""
        if self.agent_manager is not None and self.registered:
            try:
                await self.agent_manager.call_unregister_agent(BLUEZ_AGENT_PATH)
                _LOGGER.info("Precision Plex unregistered temporary BlueZ agent")
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug(
                    "Precision Plex BlueZ agent unregister failed: %r",
                    err,
                )

        if self.bus is not None and self.exported:
            try:
                self.bus.unexport(BLUEZ_AGENT_PATH, self.agent_interface)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Precision Plex BlueZ agent unexport failed: %r", err)

        if self.bus is not None:
            try:
                self.bus.disconnect()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Precision Plex BlueZ agent bus disconnect failed: %r", err)
