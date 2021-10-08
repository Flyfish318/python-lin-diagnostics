# python-lin-diagnostics
`lindiagnostics` is a pure Python 3 implementation of a LIN (Local Interconnect Network) master for the purposes of
performing diagnostic communication with slave devices in accordance with ISO-17987. An adapter class is provided to
support UDS diagnostics through the `udsoncan` library, though not all slave nodes support UDS. The library also
provides a simulated slave implementation that can be used to test ECU bus masters.

## Supported interfaces
For now, only Kvaser's LIN API, and the included simulated network drivers are supported. There are many other vendors
who provide LIN adapters for consumer PC's including Peak, and writing drivers for them should be simple enough.

## Testing
Simply use pytest from the root directory as follows
``` python -m pytest ```

## Example usage
In this example, we use `udsoncan` to read a DID over UDS using the LIN Transport Protocol.

```
simulated_network = SimulatedLinNetwork()
nad = 1
supplier_id = 2
function_id = 3
variant_id = 4
simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
master_driver = simulated_network.get_master_driver()
config = dict(udsoncan.configs.default_client_config)
config['data_identifiers'] = {0x1234: '>H'}
with LinMaster(master_driver) as lin_master:
    with LinDiagnosticsUDSConnector(lin_master, nad) as lin_diagnostic_connector:
        with Client(lin_diagnostic_connector, config=config) as uds_client:
            result = uds_client.read_data_by_identifier(0x1234)
            assert result.valid
            assert result.service_data.values[0x1234][0] == 1
```
