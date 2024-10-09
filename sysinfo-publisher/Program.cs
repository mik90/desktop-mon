using LibreHardwareMonitor.Hardware;
using System.IO.Ports;
using System.Text.Json;

public class UpdateVisitor : IVisitor
{
    public void VisitComputer(IComputer computer)
    {
        computer.Traverse(this);
    }
    public void VisitHardware(IHardware hardware)
    {
        hardware.Update();
        foreach (IHardware subHardware in hardware.SubHardware) subHardware.Accept(this);
    }
    public void VisitSensor(ISensor sensor) { }
    public void VisitParameter(IParameter parameter) { }
}

class SystemInfo
{
    public double GpuCoreTempC { get; set; }
    public double GpuHotSpotTempC { get; set; }
    public double GpuPowerWatts { get; set; }

    public double CpuCoreTempC { get; set; }
    public double CpuCcdTempC { get; set; }
    public double CpuPackagePowerWatts { get; set; }


    private void GetGpuInfo(IHardware hardware)
    {
        GpuCoreTempC = GetSensorValue(hardware, "GPU Core", SensorType.Temperature);
        GpuHotSpotTempC = GetSensorValue(hardware, "GPU Hot Spot", SensorType.Temperature);
        GpuPowerWatts = GetSensorValue(hardware, "GPU Package", SensorType.Power);
    }
    private void GetCpuInfo(IHardware hardware)
    {
        CpuCcdTempC = GetSensorValue(hardware, "CCD1 (Tdie)", SensorType.Temperature);
        CpuCoreTempC = GetSensorValue(hardware, "Core (Tctl/Tdie)", SensorType.Temperature);
        CpuPackagePowerWatts = GetSensorValue(hardware, "Package", SensorType.Power);
    }

    // Any requested value is expected to exist in the given hardware
    private static float GetSensorValue(IHardware hardware, string sensorName, SensorType sensorType)
    {
        foreach (ISensor sensor in hardware.Sensors)
        {
            if (sensor.SensorType == sensorType && sensor.Name == sensorName && sensor.Value != null)
            {
                return (float)sensor.Value;
            }
        }
        throw new MissingSensorException(sensorName, hardware);
    }

    // Any requested hardware is expected to exist in the computer
    private static IHardware FindHardwareInComputer(List<IHardware> hardwareList, HardwareType hardwareType)
    {
        return hardwareList.Find(hardware => hardware.HardwareType == hardwareType)
                       ?? throw new MissingHardwareException(hardwareType);
    }

    public SystemInfo(Computer computer)
    {
        var hardwareList = computer.Hardware.ToList();
        GetGpuInfo(FindHardwareInComputer(hardwareList, HardwareType.GpuNvidia));
        GetCpuInfo(FindHardwareInComputer(hardwareList, HardwareType.Cpu));
    }
}

public class MissingSensorException(string sensorName, IHardware hardware) : Exception($"Could not find sensor named {sensorName} in {hardware.Name}")
{
}
public class MissingHardwareException(HardwareType type) : Exception($"Could not find hardware type {type} in computer")
{
}


class MyProgram
{

    static void Main(string[] args)
    {
        var computer = new Computer
        {
            IsCpuEnabled = true,
            IsGpuEnabled = true,
            IsMemoryEnabled = true,
            IsMotherboardEnabled = true,
            IsControllerEnabled = true,
            IsNetworkEnabled = true,
            IsStorageEnabled = true
        };

        // Go to 'device manager', do "view hidden devices", then go to ports
        var port = new SerialPort
        {
            PortName = "UnknownPort",
            DataBits = 8,
            Parity = Parity.None,
            StopBits = StopBits.One,
            BaudRate = 115200,
            NewLine = "\r" // i think this is a carriage return right?
        };

        Console.CancelKeyPress += delegate
        {
            Console.WriteLine("Closing serial port...");
            port.Close();
            Console.WriteLine("Closing computer...");
            computer.Close();
            Console.WriteLine("Done.");
        };


        computer.Open();

        if (args.Length > 0)
        {
            port.PortName = args[0];
            while (!port.IsOpen)
            {
                Console.WriteLine($"Attempting to open port '{port.PortName}'...");
                try
                {
                    port.Open();
                }
                catch (FileNotFoundException)
                {
                    var sleepSeconds = 60;
                    Console.WriteLine($"Could not open port, it's probably not connected yet.\nSleeping for {sleepSeconds} seconds and trying again");
                    Thread.Sleep(TimeSpan.FromSeconds(sleepSeconds));
                }

            }
            Console.WriteLine($"Opened '{port.PortName}' successfully");
        }

        Console.WriteLine("Writing out data...");
        while (true)
        {
            computer.Accept(new UpdateVisitor());
            var systemInfo = new SystemInfo(computer);
            var serializedSystemInfo = JsonSerializer.Serialize(systemInfo);
            if (port.IsOpen)
            {
                port.WriteLine(serializedSystemInfo);
                // Record any response from the device if it has any. Useful for debugging
                if (port.BytesToRead > 0)
                {
                    Console.WriteLine($"Device said: {port.ReadLine()}");
                }
            }
            else
            {
                // If the user doesn't want to use a port, default to writing the console
                // This ends up writing ot the console if the port suddenly gets closed
                Console.WriteLine(serializedSystemInfo);
            }

            Thread.Sleep(TimeSpan.FromMilliseconds(2000));
        }


    }
}
