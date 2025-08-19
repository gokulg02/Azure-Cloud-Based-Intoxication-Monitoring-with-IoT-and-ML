import React, { useState, useEffect, useMemo, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Brush } from 'recharts';
import { ChevronRight, BarChart3, List, Loader2, ServerCrash, Search, ChevronsUpDown } from 'lucide-react';



const API_BASE_URL = "/api";

/**
 * 
 * @returns {Promise<Array<{id: string, name: string, type: string}>>} 
 */
const fetchDevices = async () => {
  const response = await fetch(`${API_BASE_URL}/devices`);
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Network response was not ok: ${errorText}`);
  }
  
  const data = await response.json();

  return data.devices.map(deviceId => ({
    id: deviceId,
    name: deviceId,
    type: 'Device' 
  }));
};

/**
 * 
 * @param {string} deviceId - 
 * @returns {Promise<Array<{timestamp: string, status: number}>>} 
 */
const fetchGraphData = async (deviceId) => {
  if (deviceId === null) {
    return []; 
  }

  
  const response = await fetch(`${API_BASE_URL}/predictions?device_id=${deviceId}`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Network response was not ok: ${errorText}`);
  }
  
  const data = await response.json();

  return data.predictions.map(p => ({
    timestamp: p.DataTime.replace(' ', 'T'),
    status: p.Prediction
  }));
};



const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const date = new Date(data.timestamp); 
    const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const statusText = data.status === 1 ? 'Drunk' : 'Sober';
    const statusColor = data.status === 1 ? 'text-red-400' : 'text-green-400';

    return (
      <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm p-3 rounded-lg border border-gray-600 shadow-lg">
        <p className="text-sm text-gray-300">{`Time: ${timeString}`}</p>
        <p className={`text-lg font-bold ${statusColor}`}>{statusText}</p>
      </div>
    );
  }
  return null;
};

const DeviceGraph = ({ data, loading, error }) => {
  const aggregatedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const minuteGroups = new Map();
    
    data.forEach(item => {
      const date = new Date(item.timestamp);
      const minuteKey = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes()).toISOString();
      
      if (!minuteGroups.has(minuteKey)) {
        minuteGroups.set(minuteKey, {
          timestamp: minuteKey,
          zeros: 0,
          ones: 0
        });
      }

      const group = minuteGroups.get(minuteKey);
      if (item.status === 1) {
        group.ones += 1;
      } else {
        group.zeros += 1;
      }
    });
    
    return Array.from(minuteGroups.values()).map(group => ({
      timestamp: group.timestamp,
      status: group.ones > group.zeros ? 1 : 0
    }));
  }, [data]);

  const formatXAxis = (tickItem) => new Date(tickItem).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <Loader2 className="animate-spin h-12 w-12 mb-4" />
        <p className="text-lg">Loading Graph Data...</p>
      </div>
    );
  }

  if (error) {
     return (
      <div className="flex flex-col items-center justify-center h-full text-red-400">
        <ServerCrash className="h-16 w-16 mb-4" />
        <h3 className="text-2xl font-semibold mb-2">Failed to Load Graph</h3>
        <p className="text-center max-w-md">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <BarChart3 className="h-16 w-16 mb-4" />
        <h3 className="text-2xl font-semibold mb-2">No Data to Display</h3>
        <p>Please select a device from the list to view its graph.</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={aggregatedData} // Use the new aggregated data
        margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
        <XAxis 
          dataKey="timestamp" 
          stroke="#A0AEC0" 
          tick={{ fontSize: 12 }} 
          tickFormatter={formatXAxis}
          interval="preserveStartEnd"
        />
        <YAxis stroke="#A0AEC0" domain={[0, 1]} ticks={[0, 1]} tickFormatter={(value) => (value === 1 ? 'Drunk' : 'Sober')} tick={{ fontSize: 12, dx: -5 }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ paddingTop: '20px' }} />
        <Line type="stepAfter" dataKey="status" stroke="#4299E1" strokeWidth={2} dot={false} name="Device Status" />
        
        {/* Interactive Brush for Zooming and Panning */}
        <Brush 
          dataKey="timestamp" 
          height={30} 
          stroke="#81E6D9" 
          fill="#2D3748"
          tickFormatter={formatXAxis}
          data={aggregatedData}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

const DeviceSelector = ({ devices, selectedDeviceId, onSelectDevice, loading, error }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef(null);

  const selectedDeviceName = useMemo(() => {
    return devices.find(d => d.id === selectedDeviceId)?.name || "Select a Device";
  }, [devices, selectedDeviceId]);

  const filteredDevices = useMemo(() => {
    if (!searchTerm) return devices;
    return devices.filter(device => device.name.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [devices, searchTerm]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 flex items-center justify-center text-gray-400">
        <Loader2 className="animate-spin h-6 w-6 mr-2" />
        <span>Loading Devices...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 flex flex-col items-center justify-center text-red-400">
        <ServerCrash className="h-12 w-12 mb-4" />
        <h3 className="text-xl font-semibold mb-2 text-center">Failed to Load Devices</h3>
        <p className="text-center text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4" ref={dropdownRef}>
      <h2 className="text-xl font-bold text-white mb-4 flex items-center">
        <List className="mr-2 h-5 w-5" />
        Select Device
      </h2>
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full bg-gray-700 p-3 rounded-md text-left flex justify-between items-center transition-colors hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <span className={selectedDeviceId ? 'text-white' : 'text-gray-400'}>{selectedDeviceName}</span>
          <ChevronsUpDown className="h-5 w-5 text-gray-400" />
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-2 w-full bg-gray-700 rounded-md shadow-lg border border-gray-600">
            <div className="p-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search devices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-gray-800 rounded-md p-2 pl-10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <ul className="max-h-60 overflow-y-auto p-2">
              {filteredDevices.length > 0 ? (
                filteredDevices.map(device => (
                  <li
                    key={device.id}
                    onClick={() => {
                      onSelectDevice(device.id);
                      setIsOpen(false);
                      setSearchTerm("");
                    }}
                    className={`p-3 rounded-md cursor-pointer flex justify-between items-center transition-colors ${
                      selectedDeviceId === device.id
                        ? 'bg-blue-600 text-white'
                        : 'hover:bg-gray-600 text-gray-300'
                    }`}
                  >
                    {device.name}
                    {selectedDeviceId === device.id && <ChevronRight className="h-5 w-5" />}
                  </li>
                ))
              ) : (
                <li className="p-3 text-center text-gray-400">No devices found.</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default function App() {
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [graphData, setGraphData] = useState([]);
  const [loadingDevices, setLoadingDevices] = useState(true);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [deviceError, setDeviceError] = useState(null);
  const [graphError, setGraphError] = useState(null);

  useEffect(() => {
    setLoadingDevices(true);
    setDeviceError(null);
    fetchDevices()
      .then(data => {
        setDevices(data);
      })
      .catch(err => {
        console.error("Failed to fetch devices:", err);
        setDeviceError(err.message);
      })
      .finally(() => {
        setLoadingDevices(false);
      });
  }, []);

  useEffect(() => {
    if (selectedDeviceId === null) {
      setGraphData([]);
      return;
    }
    setLoadingGraph(true);
    setGraphError(null);
    fetchGraphData(selectedDeviceId)
      .then(data => {
        setGraphData(data);
      })
      .catch(err => {
        console.error("Failed to fetch graph data:", err);
        setGraphError(err.message);
      })
      .finally(() => {
        setLoadingGraph(false);
      });
  }, [selectedDeviceId]);

  const selectedDeviceName = useMemo(() => {
    if (!devices || devices.length === 0) return 'No Device Selected';
    return devices.find(d => d.id === selectedDeviceId)?.name || 'No Device Selected';
  }, [devices, selectedDeviceId]);

  return (
    <div className="bg-gray-900 text-white min-h-screen font-sans p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-4xl font-extrabold tracking-tight text-center sm:text-left">Intoxication Monitering Dashboard </h1>
          <p className="text-gray-400 text-center sm:text-left">Real-time monitoring of intoxication status</p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <DeviceSelector 
              devices={devices}
              selectedDeviceId={selectedDeviceId}
              onSelectDevice={setSelectedDeviceId}
              loading={loadingDevices}
              error={deviceError}
            />
          </div>

          <div className="lg:col-span-2 bg-gray-800 rounded-lg p-4 sm:p-6 min-h-[500px] flex flex-col">
            <h2 className="text-2xl font-bold text-white mb-2">Device: <span className="text-blue-400">{selectedDeviceName}</span></h2>
            <p className="text-sm text-gray-400 mb-4">Displaying the intoxication prediction data. Drag the slider below to zoom.</p>
            <div className="flex-grow">
              <DeviceGraph data={graphData} loading={loadingGraph} error={graphError} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
