from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, DISPATCHER_POLICY_EXECUTED, DISPATCHER_DECISION_UPDATED


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


class PolicyStatsSensor(SensorEntity):
    _attr_name = "HA Governance Policy Stats"
    _attr_unique_id = "ha_governance_policy_stats"
    _attr_icon = "mdi:chart-box-outline"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._unsub = None

    @property
    def native_value(self) -> int:
        data = self._hass.data.get(DOMAIN, {})
        stats = data.get("policy_stats", {})
        return len(stats)

    @property
    def extra_state_attributes(self):
        data = self._hass.data.get(DOMAIN, {})
        stats = data.get("policy_stats", {})
        return stats

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "ha_governance")},
            name="HA Governance",
            manufacturer="Starsurfer78",
            model="Governance Engine",
        )

    async def async_added_to_hass(self) -> None:
        async def _handle_update(policy_name):
            self.async_write_ha_state()

        self._unsub = async_dispatcher_connect(
            self._hass,
            DISPATCHER_POLICY_EXECUTED,
            _handle_update,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None


class LastDecisionSensor(SensorEntity):
    _attr_name = "HA Governance Last Decision"
    _attr_unique_id = "ha_governance_last_decision"
    _attr_icon = "mdi:account-eye-outline"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._unsub = None

    @property
    def native_value(self):
        data = self._hass.data.get(DOMAIN, {})
        decision = data.get("last_decision")
        if not decision:
            return None
        return decision.get("final_policy")

    @property
    def extra_state_attributes(self):
        data = self._hass.data.get(DOMAIN, {})
        decision = data.get("last_decision") or {}
        return {
            "timestamp": decision.get("timestamp"),
            "event_type": decision.get("event_type"),
            "entity_id": decision.get("entity_id"),
            "policy_snapshot_hash": decision.get("policy_snapshot_hash"),
            "enforcement_result": decision.get("enforcement_result"),
            "context_id": decision.get("context_id"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "ha_governance")},
            name="HA Governance",
            manufacturer="Starsurfer78",
            model="Governance Engine",
        )

    async def async_added_to_hass(self) -> None:
        self._unsub = async_dispatcher_connect(
            self._hass,
            DISPATCHER_DECISION_UPDATED,
            self.async_write_ha_state,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities(
        [
            PolicyCountSensor(hass),
            PolicyStatsSensor(hass),
            LastDecisionSensor(hass),
        ],
        True,
    )
