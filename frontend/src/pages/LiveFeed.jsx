import React, { useState, useEffect } from 'react';
import { Maximize2, Minimize2, Video, Wifi, Settings, X, Save } from 'lucide-react';
import axios from 'axios';

const LiveFeed = () => {
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [configModal, setConfigModal] = useState(null); // { id, name, source }
    const [newSource, setNewSource] = useState('');

    useEffect(() => {
        loadCameras();
    }, []);

    const loadCameras = () => {
        fetch('http://localhost:5001/api/cameras')
            .then(res => res.json())
            .then(data => setCameras(data))
            .catch(err => console.error("Failed to load cameras", err));
    };

    const toggleMaximize = (camId) => {
        if (selectedCamera === camId) {
            setSelectedCamera(null);
        } else {
            setSelectedCamera(camId);
        }
    };

    const openConfig = (cam) => {
        setConfigModal(cam);
        setNewSource(cam.source);
    };

    const saveConfig = async () => {
        if (!configModal) return;

        const updatedCameras = cameras.map(c =>
            c.id === configModal.id ? { ...c, source: newSource } : c
        );

        try {
            await axios.post('http://localhost:5001/api/cameras', updatedCameras);
            setCameras(updatedCameras);
            setConfigModal(null);
            alert("Camera configuration updated!");
        } catch (error) {
            console.error("Failed to update config", error);
            alert("Failed to update configuration");
        }
    };

    return (
        <div className="p-6 relative">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
                <Video className="w-8 h-8 text-neon-blue" />
                Live Surveillance
            </h1>

            {/* Camera Grid */}
            <div className={`grid gap-6 ${selectedCamera !== null ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2'}`}>
                {cameras.map((cam) => {
                    if (selectedCamera !== null && selectedCamera !== cam.id) return null;

                    return (
                        <div key={cam.id} className={`relative bg-glass-dark border border-white/10 rounded-xl overflow-hidden shadow-2xl transition-all duration-300 ${selectedCamera === cam.id ? 'h-[80vh]' : 'h-[400px]'}`}>
                            {/* Header */}
                            <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/80 to-transparent z-10 flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full ${cam.source === 0 ? 'bg-green-500' : 'bg-blue-500'} animate-pulse`}></div>
                                    <span className="text-white font-mono text-sm tracking-wider">{cam.name.toUpperCase()}</span>
                                    {cam.source !== 0 && <Wifi className="w-3 h-3 text-gray-400" />}
                                </div>
                                <div className="flex items-center gap-2">
                                    {/* Config Button (Only for IP Cams) */}
                                    {cam.source !== 0 && (
                                        <button
                                            onClick={() => openConfig(cam)}
                                            className="p-2 hover:bg-white/10 rounded-full text-white transition-colors"
                                            title="Configure Camera IP"
                                        >
                                            <Settings size={20} />
                                        </button>
                                    )}
                                    <button
                                        onClick={() => toggleMaximize(cam.id)}
                                        className="p-2 hover:bg-white/10 rounded-full text-white transition-colors"
                                    >
                                        {selectedCamera === cam.id ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
                                    </button>
                                </div>
                            </div>

                            {/* Video Feed */}
                            <img
                                src={`http://localhost:5001/video_feed/${cam.id}`}
                                alt={cam.name}
                                className="w-full h-full object-cover"
                            />

                            {/* HUD Overlay */}
                            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent pointer-events-none">
                                <div className="flex justify-between text-[10px] text-neon-blue font-mono">
                                    <span>CAM_ID: {cam.id.toString().padStart(3, '0')}</span>
                                    <span>SIGNAL: STABLE</span>
                                    <span>REC: ON</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Config Modal */}
            {configModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-gray-900 border border-white/10 p-6 rounded-2xl w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Settings className="text-neon-blue" />
                                Configure Camera
                            </h2>
                            <button onClick={() => setConfigModal(null)} className="text-gray-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-gray-400 text-sm mb-2">Camera Name</label>
                                <input
                                    type="text"
                                    value={configModal.name}
                                    disabled
                                    className="w-full bg-black/50 border border-white/10 rounded-lg p-3 text-gray-500 cursor-not-allowed"
                                />
                            </div>
                            <div>
                                <label className="block text-gray-400 text-sm mb-2">IP Address / URL</label>
                                <input
                                    type="text"
                                    value={newSource}
                                    onChange={(e) => setNewSource(e.target.value)}
                                    placeholder="http://192.168.x.x:8080/video"
                                    className="w-full bg-black/50 border border-neon-blue/50 rounded-lg p-3 text-white focus:outline-none focus:ring-2 focus:ring-neon-blue"
                                />
                                <p className="text-xs text-gray-500 mt-2">
                                    Enter the full URL from your IP Webcam app (e.g., http://10.150.144.63:8080/video)
                                </p>
                            </div>
                        </div>

                        <div className="mt-8 flex justify-end gap-3">
                            <button
                                onClick={() => setConfigModal(null)}
                                className="px-4 py-2 rounded-lg text-gray-400 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={saveConfig}
                                className="px-6 py-2 bg-neon-blue text-black font-bold rounded-lg hover:bg-blue-400 transition-colors flex items-center gap-2"
                            >
                                <Save size={18} />
                                Save & Connect
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {cameras.length === 0 && (
                <div className="text-center text-gray-400 mt-20">
                    <p>Loading cameras...</p>
                </div>
            )}
        </div>
    );
};

export default LiveFeed;
