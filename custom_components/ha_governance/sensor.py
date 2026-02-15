from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN


class PolicyCountSensor(SensorEntity):
    _attr_name = "HA Governance Policy Count"
    _attr_unique_id = "ha_governance_policy_count"
    _attr_icon = "mdi:shield-check"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._unsub = None

    @property
    def native_value(self) -> int:
        data = self._hass.data.get(DOMAIN, {})
        policies = data.get("policies", [])
        return len(policies)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "ha_governance")},
            name="HA Governance",
            manufacturer="Starsurfer78",
            model="Governance Engine",
        )

    async def async_added_to_hass(self) -> None:
        from .const import DISPATCHER_POLICIES_UPDATED

        self._unsub = async_dispatcher_connect(
            self._hass,
            DISPATCHER_POLICIES_UPDATED,
            self.async_write_ha_state,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities([PolicyCountSensor(hass)], True)
