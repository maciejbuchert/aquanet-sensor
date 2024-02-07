"""Platform for sensor integration."""
from __future__ import annotations

import logging
import string
from datetime import timedelta
from typing import Callable, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, VOLUME_CUBIC_METERS, METER_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, HomeAssistantType

from .AquanetApi import AquanetApi

_LOGGER = logging.getLogger(__name__)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})
SCAN_INTERVAL = timedelta(hours=8)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities,
):
    user = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    api = AquanetApi(user, password)
    try:
        pgps = await hass.async_add_executor_job(api.meterList)
    except Exception:
        raise ValueError

    for x in pgps.ppg_list:
        meter_id = x.meter_number
        async_add_entities(
            [AquanetSensor(hass, api, meter_id, x.id_local),
             AquanetInvoiceSensor(hass, api, meter_id, x.id_local),
             AquanetCostTrackingSensor(hass, api, meter_id, x.id_local)],
            update_before_add=True)


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    api = AquanetApi(config.get(CONF_USERNAME), config.get(CONF_PASSWORD))
    async_add_entities(
        [AquanetSensor(hass, api, config.get(METER_ID))], update_before_add=True)


class AquanetSensor(SensorEntity):
    def __init__(self, hass, api: AquanetApi, meter_id: string) -> None:
        self._attr_native_unit_of_measurement = VOLUME_CUBIC_METERS
        self._attr_device_class = SensorDeviceClass.GAS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._state: MeterReading | None = None
        self.hass = hass
        self.api = api
        self.meter_id = meter_id
        self.entity_name = "Aquanet Water Sensor " + meter_id

    @property
    def unique_id(self) -> str | None:
        return "aquanet_sensor" + self.meter_id + "_" + str(self.id_local)

    @property
    def device_info(self):
        return {
            "identifiers": {("aquanet_water_sensor", self.meter_id)},
            "name": f"AQUANET WATER METER ID {self.meter_id}",
            "manufacturer": "AQUANET",
            "model": self.meter_id,
            "via_device": None,
        }

    @property
    def name(self) -> str:
        return self.entity_name

    @property
    def state(self):
        if self._state is None:
            return None
        return self._state.value

    @property
    def extra_state_attributes(self):
        attrs = dict()
        if self._state is not None:
            attrs["wear"] = self._state.wear
            attrs["wear_unit_of_measurment"] = VOLUME_CUBIC_METERS
        return attrs

    async def async_update(self):
        val = self.latestMeterReading
        if val is not None:
            latest_meter_reading: MeterReading = await self.hass.async_add_executor_job(self.latestMeterReading)
            self._state = latest_meter_reading

    def latestMeterReading(self):
        return self.api.consumptionChart(self.meter_id)