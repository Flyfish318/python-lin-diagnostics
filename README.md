# python-lin-diagnostics
`lindiagnostics` is a pure Python 3 implementation of a LIN (Local Interconnect Network) master for the purposes of performing diagnostic communication with slave devices in accordance with ISO-17987.
An adapter class is provided to support UDS diagnostics through the `udsoncan` library, though not all slave nodes support UDS.
The library also provides a simulated slave implementation that can be used to test ECU bus masters.

A version of the LIN 2.1 specification is publically available at:
https://lin-cia.org/fileadmin/microsites/lin-cia.org/resources/documents/LIN-Spec_Pac2_1.pdf

## Supported interfaces
For now, only Kvaser's LIN API, and the included simulated network drivers are supported.
There are many other vendors who provide LIN adapters for consumer PC's including Peak, and writing drivers for them should be simple enough.
For Peak, the PLIN API (https://www.peak-system.com/PLIN-API.444.0.html?&L=1) should do the trick.

### Kvaser Setup
1. On both Windows and Linux, you'll need to install the CANlib SDK (The Linux SDK includes the drivers).
   The latest can be found on Kvaser's download page: https://www.kvaser.com/download/
2. On Windows, you may need to install the CAN drivers (from the same page).
3. Kvaser LIN adapters use a DB9 connector with a specific pinout and expects the LIN reference voltage and ground to be provided.
   The LIN Spec allows reference voltages (V<sub>BAT</sub>) from 8 to 18V.
   The Kvaser manual shows the pinout is:
  * Ground: Pin 3
  * Shield: Pin 5 (Optional)
  * LIN Bus: Pin 7
  * Reference Voltage: Pin 9

## Testing
To run the unit tests (using simulated LIN master and slaves), simply use pytest from the root directory as follows:
``` python -m pytest ```

If you have two LIN adapters (such as a Kvaser Hybrid Pro 2x CAN/LIN), a simple test harness can be made with a DB9 Y adapter (2x female, 1x male) and a DB9 breakout board.
Simply attach connect everything and apply > +8V between pins 9 (+) and 3 (-) on the breakout board using a bench power supply or battery.

Alternatively, you can use the simulated network provided in this library.

## Example UDS with pure simulated
In this example, we create a simulated LIN network with a simulated slave attached.

.. code-block:: python

   from lindiagnostics import LinMaster
   from lindiagnostics.drivers import SimulatedLinNetwork
   from lindiagnostics.connectors import LinDiagnosticsUDSConnector
   from udsoncan.client import Client
   import udsoncan

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
                uds_client.tester_present()
                uds_client.start_routine(0x1, data=bytes(10))
                uds_client.read_data_by_identifier(0x1234)

## Example using 2x Kvaser Channels Connected Together
In this example, we simulate a LIN Slave attached to Kvaser Virtual Channel 0, and interrogate it with a LIN Master attached to Kvaser Virtual Channel 1.
The slave will run as a thread, handling its logic every 10 milliseconds.
We use the `udsoncan` library to handle the UDS layer.

.. code-block:: python

   from lindiagnostics import LinMaster, LinSlave, LinSlaveThread
   from lindiagnostics.drivers import KvaserLinDriver
   from lindiagnostics.connectors import LinDiagnosticsUDSConnector
   from udsoncan.client import Client
   import udsoncan

   nad = 1
   supplier_id = 2
   function_id = 3
   variant_id = 4

   slave_driver = KvaserLinDriver(0, True)
   master_driver = KvaserLinDriver(1, False)
   lin_slave = LinSlave(nad, supplier_id, function_id, variant_id, driver=slave_driver)
   with LinSlaveThread(lin_slave) as lin_slave_thread:
       with LinMaster(master_driver) as lin_master:
           with LinDiagnosticsUDSConnector(lin_master, nad) as lin_diagnostic_connector:
               config = dict(udsoncan.configs.default_client_config)
               config['data_identifiers'] = {0x1234: '>H'}
               with Client(lin_diagnostic_connector, config=config) as uds_client:
                   uds_client.tester_present()
                   uds_client.start_routine(0x1, data=bytes(10))
                   uds_client.read_data_by_identifier(0x1234)