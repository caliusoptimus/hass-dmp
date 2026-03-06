"""Test config flow for DMP integration."""
import pytest
from unittest.mock import patch, Mock
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.dmp.config_flow import DMPCustomConfigFlow, OptionsFlowHandler
from custom_components.dmp.const import (
    CONF_ZONES,
    CONF_ZONE_NAME,
    CONF_ZONE_NUMBER,
    CONF_ZONE_CLASS,
    CONF_HOME_AREA,
    CONF_AWAY_AREA,
    CONF_ADD_ANOTHER,
)


pytestmark = pytest.mark.asyncio
async def test_form_user_step(hass: HomeAssistant):
    """Test we get the user form."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    
    result = await flow.async_step_user()
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"

async def test_form_user_to_areas(hass: HomeAssistant):
    """Test user input progresses to areas step."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    
    user_input = {
        "panel_name": "Test Panel",
        "ip": "192.168.1.100",
        "listen_port": 40002,
        "remote_port": 40001,
        "account_number": "12345"
    }
    
    result = await flow.async_step_user(user_input)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "areas"
    assert flow.data == user_input
    assert flow.data[CONF_ZONES] == []

async def test_form_areas_to_zones(hass: HomeAssistant):
    """Test areas input progresses to zones step."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {"existing": "data", CONF_ZONES: []}
    
    areas_input = {
        CONF_HOME_AREA: "01",
        CONF_AWAY_AREA: "02"
    }
    
    result = await flow.async_step_areas(areas_input)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zones"
    assert flow.data[CONF_HOME_AREA] == "01"
    assert flow.data[CONF_AWAY_AREA] == "02"

async def test_form_areas_add_another(hass: HomeAssistant):
    """Test areas with add_another stays on areas step."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {"existing": "data", CONF_ZONES: []}
    
    areas_input = {
        CONF_HOME_AREA: "01",
        CONF_AWAY_AREA: "02",
        CONF_ADD_ANOTHER: True
    }
    
    result = await flow.async_step_areas(areas_input)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "areas"
    assert CONF_ADD_ANOTHER not in flow.data

async def test_form_zones_creates_entry(hass: HomeAssistant):
    """Test zones input creates config entry."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {
        "panel_name": "Test Panel",
        "ip": "192.168.1.100",
        CONF_ZONES: []
    }
    
    zones_input = {
        CONF_ZONE_NAME: "Front Door",
        CONF_ZONE_NUMBER: "001",
        CONF_ZONE_CLASS: "wired_door"
    }
    
    with patch.object(flow, 'async_create_entry', return_value=None) as mock_create:
        await flow.async_step_zones(zones_input)
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs['title'] == "Test Panel"
        assert len(call_args.kwargs['data'][CONF_ZONES]) == 1
        assert call_args.kwargs['data'][CONF_ZONES][0] == {
            "zone_name": "Front Door",
            "zone_number": "001",
            "zone_class": "wired_door"
        }

async def test_form_zones_add_another(hass: HomeAssistant):
    """Test zones with add_another stays on zones step."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {
        "panel_name": "Test Panel",
        CONF_ZONES: []
    }
    
    zones_input = {
        CONF_ZONE_NAME: "Front Door",
        CONF_ZONE_NUMBER: "001",
        CONF_ZONE_CLASS: "wired_door",
        CONF_ADD_ANOTHER: True
    }
    
    result = await flow.async_step_zones(zones_input)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zones"
    assert len(flow.data[CONF_ZONES]) == 1
    assert flow.data[CONF_ZONES][0][CONF_ADD_ANOTHER]

async def test_form_zones_multiple_zones(hass: HomeAssistant):
    """Test adding multiple zones."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {
        "panel_name": "Test Panel",
        CONF_ZONES: [{
            "zone_name": "Front Door",
            "zone_number": "001",
            "zone_class": "wired_door"
        }]
    }
    
    zones_input = {
        CONF_ZONE_NAME: "Motion Sensor",
        CONF_ZONE_NUMBER: "002",
        CONF_ZONE_CLASS: "wired_motion",
        CONF_ADD_ANOTHER: True
    }
    
    result = await flow.async_step_zones(zones_input)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zones"
    assert len(flow.data[CONF_ZONES]) == 2

async def test_form_zones_creates_entry_via_csv(hass: HomeAssistant):
    """Test zones step supports CSV import without manual zone fields."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {
        "panel_name": "Test Panel",
        CONF_ZONES: []
    }

    zones_input = {
        "zones_csv": (
            "zone_number,zone_name,zone_class\n"
            "001,Front Door,wired_door\n"
            "002,Living Motion,wired_motion\n"
        )
    }

    with patch.object(flow, 'async_create_entry', return_value=None) as mock_create:
        await flow.async_step_zones(zones_input)
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        zones = call_args.kwargs["data"][CONF_ZONES]
        assert len(zones) == 2
        assert zones[0][CONF_ZONE_NUMBER] == "001"
        assert zones[1][CONF_ZONE_CLASS] == "wired_motion"

async def test_form_zones_missing_manual_fields_error(hass: HomeAssistant):
    """Test zones step requires manual fields if CSV is not provided."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {
        "panel_name": "Test Panel",
        CONF_ZONES: []
    }

    result = await flow.async_step_zones(
        {
            CONF_ZONE_NAME: "",
            CONF_ZONE_NUMBER: "",
            CONF_ZONE_CLASS: "wired_door",
        }
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zones"
    assert result["errors"]["base"] == "missing_zone_fields"

async def test_form_zones_invalid_csv_error(hass: HomeAssistant):
    """Test zones step reports invalid CSV errors."""
    flow = DMPCustomConfigFlow()
    flow.hass = hass
    flow.data = {
        "panel_name": "Test Panel",
        CONF_ZONES: []
    }

    result = await flow.async_step_zones(
        {"zones_csv": "zone_number,zone_name\n001,MissingClass\n"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zones"
    assert result["errors"]["base"] == "invalid_zones_csv"



@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = Mock(spec=config_entries.ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        "panel_name": "Test Panel",
        CONF_ZONES: [
            {
                CONF_ZONE_NAME: "Front Door",
                CONF_ZONE_NUMBER: "001",
                CONF_ZONE_CLASS: "wired_door"
            },
            {
                CONF_ZONE_NAME: "Motion Sensor",
                CONF_ZONE_NUMBER: "002", 
                CONF_ZONE_CLASS: "wired_motion"
            }
        ]
    }
    return entry

@pytest.fixture
def mock_entity_registry():
    """Mock entity registry."""
    with patch("homeassistant.helpers.entity_registry.async_get") as mock_get:
        registry = Mock()
        registry.async_get_entity_id.return_value = None
        mock_get.return_value = registry
        yield registry

async def test_options_flow_init(hass: HomeAssistant, mock_config_entry, mock_entity_registry):
    """Test options flow initialization."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    
    entries = []
    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = entries
        
        result = await flow.async_step_init()
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

async def test_options_flow_remove_zone(hass: HomeAssistant, mock_config_entry, mock_entity_registry):
    """Test removing a zone."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    
    user_input = {
        CONF_ZONES: ["001"], 
        CONF_ZONE_NAME: "",
        CONF_ZONE_NUMBER: "",
        CONF_ZONE_CLASS: "default"
    }
    
    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []
        
        with patch.object(flow, 'async_create_entry', return_value=None) as mock_create:
            await flow.async_step_init(user_input)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert len(call_args.kwargs['data'][CONF_ZONES]) == 1
            assert call_args.kwargs['data'][CONF_ZONES][0][CONF_ZONE_NUMBER] == "001"

async def test_options_flow_add_zone(hass: HomeAssistant, mock_config_entry, mock_entity_registry):
    """Test adding a new zone."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    
    user_input = {
        CONF_ZONES: ["001", "002"],
        CONF_ZONE_NAME: "Back Door",
        CONF_ZONE_NUMBER: "003",
        CONF_ZONE_CLASS: "wired_door"
    }
    
    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []
        
        with patch.object(flow, 'async_create_entry', return_value=None) as mock_create:
            await flow.async_step_init(user_input)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert len(call_args.kwargs['data'][CONF_ZONES]) == 3
            new_zone = next(z for z in call_args.kwargs['data'][CONF_ZONES] if z[CONF_ZONE_NUMBER] == "003")
            assert new_zone[CONF_ZONE_NAME] == "Back Door"
            assert new_zone[CONF_ZONE_CLASS] == "wired_door"

async def test_options_flow_no_changes(hass: HomeAssistant, mock_config_entry, mock_entity_registry):
    """Test options flow with no changes."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    
    user_input = {
        CONF_ZONES: ["001", "002"],
        CONF_ZONE_NAME: "",
        CONF_ZONE_NUMBER: "",
        CONF_ZONE_CLASS: "default"
    }
    
    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []
        
        with patch.object(flow, 'async_create_entry', return_value=None) as mock_create:
            await flow.async_step_init(user_input)           
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert len(call_args.kwargs['data'][CONF_ZONES]) == 2

async def test_options_flow_handles_missing_optional_add_fields(
    hass: HomeAssistant, mock_config_entry, mock_entity_registry
):
    """Options flow should not fail when optional add-zone fields are omitted."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass

    user_input = {
        CONF_ZONES: ["001", "002"],
    }

    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []

        with patch.object(flow, 'async_create_entry', return_value=None) as mock_create:
            await flow.async_step_init(user_input)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert len(call_args.kwargs['data'][CONF_ZONES]) == 2

async def test_options_flow_zone_dict_creation(hass: HomeAssistant, mock_config_entry, mock_entity_registry):
    """Test zone dictionary is created correctly."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    
    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []
        
        result = await flow.async_step_init()
        
        schema = result["data_schema"]
        assert any(key for key in schema.schema if hasattr(key, 'schema') and CONF_ZONES in str(key))

async def test_options_flow_import_zones_csv_replace(
    hass: HomeAssistant, mock_config_entry, mock_entity_registry
):
    """CSV import can replace all zones."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass

    user_input = {
        "zones_csv": (
            "zone_number,zone_name,zone_class\n"
            "010,CSV Door,wired_door\n"
            "011,CSV Motion,wired_motion\n"
        ),
        "zones_csv_replace": True,
    }

    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []

        with patch.object(flow, "async_create_entry", return_value=None) as mock_create:
            await flow.async_step_init(user_input)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            zones = call_args.kwargs["data"][CONF_ZONES]
            assert len(zones) == 2
            assert zones[0][CONF_ZONE_NUMBER] == "010"
            assert zones[1][CONF_ZONE_CLASS] == "wired_motion"

async def test_options_flow_import_zones_csv_merge(
    hass: HomeAssistant, mock_config_entry, mock_entity_registry
):
    """CSV import can merge with existing zones when replace is disabled."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass

    user_input = {
        "zones_csv": "zone_number,zone_name,zone_class\n003,Back Door,wired_door\n",
        "zones_csv_replace": False,
    }

    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []

        with patch.object(flow, "async_create_entry", return_value=None) as mock_create:
            await flow.async_step_init(user_input)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            zones = call_args.kwargs["data"][CONF_ZONES]
            assert len(zones) == 3
            assert any(z[CONF_ZONE_NUMBER] == "003" for z in zones)

async def test_options_flow_import_zones_csv_invalid(
    hass: HomeAssistant, mock_config_entry, mock_entity_registry
):
    """Invalid CSV should return form with CSV error."""
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass

    user_input = {
        "zones_csv": "zone_number,zone_name\n001,MissingClass\n",
        "zones_csv_replace": True,
    }

    with patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry") as mock_entries:
        mock_entries.return_value = []
        result = await flow.async_step_init(user_input)
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_zones_csv"

@pytest.mark.asyncio
async def test_async_get_options_flow(hass: HomeAssistant, mock_config_entry):
    """Verify options flow retrieval from the config flow class."""
    flow = DMPCustomConfigFlow()
    options_flow = flow.async_get_options_flow(mock_config_entry)
    options_flow.hass = hass
    assert isinstance(options_flow, OptionsFlowHandler)
    assert options_flow._config_entry is mock_config_entry
