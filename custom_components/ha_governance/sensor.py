from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN


class PolicyCountSensor(SensorEntity):
    _attr_name = "HA Governance Policy Count"
    _attr_unique_id = "ha_governance_policy_count"
    _attr_icon = "mdi:shield-check"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    @property
    def native_value(self) -> int:
        data = self._hass.data.get(DOMAIN, {})
        policies = data.get("policies", [])
        return len(policies)

    async def async_added_to_hass(self) -> None:
        data = self._hass.data.setdefault(DOMAIN, {})
        sensors = data.setdefault("policy_sensors", [])
        sensors.append(self)

    async def async_will_remove_from_hass(self) -> None:
        data = self._hass.data.get(DOMAIN, {})
        sensors = data.get("policy_sensors", [])
        if isinstance(sensors, list) and self in sensors:
            sensors.remove(self)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities([PolicyCountSensor(hass)], True)

