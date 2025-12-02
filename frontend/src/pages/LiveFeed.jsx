import React, { useState, useEffect } from 'react';
import { Maximize2, Minimize2, Video, Wifi } from 'lucide-react';

const LiveFeed = () => {
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);

    useEffect(() => {
        fetch('http://localhost:5001/api/cameras')
            .then(res => res.json())
            .then(data => setCameras(data))
            .catch(err => console.error("Failed to load cameras", err));
    }, []);

    const toggleMaximize = (camId) => {
        if (selectedCamera === camId) {
            setSelectedCamera(null);
        } else {
            setSelectedCamera(camId);
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
                <Video className="w-8 h-8 text-neon-blue" />
                Live Surveillance
            </h1>

            {/* Camera Grid */}
            <div className={`grid gap-6 ${selectedCamera !== null ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2'}`}>
                {cameras.map((cam) => {
                    // If a camera is selected, hide others
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
                                <button
                                    onClick={() => toggleMaximize(cam.id)}
                                    className="p-2 hover:bg-white/10 rounded-full text-white transition-colors"
                                >
                                    {selectedCamera === cam.id ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
                                </button>
                            </div>

                            {/* Video Feed */}
                            <img
                                src={`http://localhost:5001/video_feed/${cam.id}`}
                                alt={cam.name}
                                className="w-full h-full object-cover"
                            />

                            {/* HUD Overlay (Decorative) */}
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

            {cameras.length === 0 && (
                <div className="text-center text-gray-400 mt-20">
                    <p>Loading cameras...</p>
                </div>
            )}
        </div>
    );
};

export default LiveFeed;
