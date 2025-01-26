"""The tests for the Buienradar sensor platform."""

from http import HTTPStatus

from homeassistant.components.buienradar.const import DOMAIN
from homeassistant.components.buienradar.sensor import BrSensor, SensorEntityDescription
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker

TEST_LONGITUDE = 51.5288504
TEST_LATITUDE = 5.4002156

CONDITIONS = ["stationname", "temperature"]
TEST_CFG_DATA = {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE}
DESCRIPTIONS = {
    "stationname": SensorEntityDescription(key="stationname", name="Station Name"),
    "temperature": SensorEntityDescription(key="temperature", name="Temperature"),
}
CLIENT_NAME = "TestClient"  # Example client name


async def test_smoke_test_setup_component(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Smoke test for successfully set-up with default config."""
    aioclient_mock.get(
        "https://data.buienradar.nl/2.0/feed/json", status=HTTPStatus.NOT_FOUND
    )
    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id="TEST_ID", data=TEST_CFG_DATA)
    mock_entry.add_to_hass(hass)

    # Register entities
    for cond in CONDITIONS:
        entity_registry.async_get_or_create(
            domain="sensor",
            platform="buienradar",
            unique_id=f"{TEST_LATITUDE:2.6f}{TEST_LONGITUDE:2.6f}{cond}",
            config_entry=mock_entry,
            original_name=f"Buienradar {cond}",
        )
    await hass.async_block_till_done()

    # Set up the mock entry
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    # Verify sensor states
    for cond in CONDITIONS:
        state = hass.states.get(f"sensor.buienradar_5_40021651_528850{cond}")
        assert state.state == "unknown"


async def test_load_data_without_new_measurement(hass: HomeAssistant) -> None:
    """Test _load_data without new measurement."""
    coordinates = {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE}

    br_sensor = BrSensor(
        client_name=CLIENT_NAME,
        coordinates=coordinates,
        description=DESCRIPTIONS["temperature"],
    )

    # Simulate the data response without a new measurement
    no_new_data = {
        "stationname": "Test Station",
        "temperature": None,  # No new measurement
    }

    # Call _load_data without await since it is not async
    result = br_sensor._load_data(no_new_data)

    # Assert that the state remains None
    assert result is False  # Ensure no update occurred
    assert br_sensor.state is None  # Check that the state remains None


async def test_load_data_with_invalid_measurement(hass: HomeAssistant) -> None:
    """Test _load_data with invalid measurement (e.g., NaN)."""
    coordinates = {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE}

    br_sensor = BrSensor(
        client_name=CLIENT_NAME,
        coordinates=coordinates,
        description=DESCRIPTIONS["temperature"],
    )

    # Simulate the data response with an invalid temperature measurement
    invalid_data = {
        "stationname": "Test Station",
        "temperature": float("nan"),  # Invalid measurement
    }

    # Call _load_data
    result = br_sensor._load_data(invalid_data)

    # Assert that the state does not update
    assert result is False  # Ensure no update occurred
    assert br_sensor.state is None  # Check that the state remains None


async def test_load_data_with_missing_keys(hass: HomeAssistant) -> None:
    """Test _load_data with missing keys in the data."""
    coordinates = {CONF_LATITUDE: TEST_LATITUDE, CONF_LONGITUDE: TEST_LONGITUDE}

    br_sensor = BrSensor(
        client_name=CLIENT_NAME,
        coordinates=coordinates,
        description=DESCRIPTIONS["temperature"],
    )

    # Simulate the data response with missing keys
    missing_data = {
        "stationname": "Test Station",
        # "temperature" key is missing
    }

    # Call _load_data
    result = br_sensor._load_data(missing_data)

    # Assert that the state does not update
    assert result is False  # Ensure no update occurred
    assert br_sensor.state is None  # Check that the state remains None
