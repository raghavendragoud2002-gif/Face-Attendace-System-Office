import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit2, Trash2, X, Save } from 'lucide-react';
import axios from 'axios';

const Employees = () => {
    const [employees, setEmployees] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [currentId, setCurrentId] = useState(null);

    const [formData, setFormData] = useState({
        name: '',
        employee_id: '',
        department: '',
        designation: '',
        email: '',
        file: null
    });

    useEffect(() => {
        fetchEmployees();
    }, []);

    const fetchEmployees = async () => {
        try {
            const res = await axios.get('http://localhost:5001/api/employees');
            setEmployees(res.data);
        } catch (err) {
            console.error("Error fetching employees:", err);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e) => {
        setFormData(prev => ({ ...prev, file: e.target.files[0] }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (isEditing) {
            try {
                await axios.put(`http://localhost:5001/api/employees/${currentId}`, formData);
                alert("Employee updated successfully!");
                closeModal();
                fetchEmployees();
            } catch (err) {
                alert("Error updating employee: " + err.message);
            }
        } else {
            if (!formData.file) {
                alert("Please upload a face photo.");
                return;
            }

            const data = new FormData();
            Object.keys(formData).forEach(key => {
                data.append(key, formData[key]);
            });

            try {
                await axios.post('http://localhost:5001/api/employees', data, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                alert("Employee added successfully!");
                closeModal();
                fetchEmployees();
            } catch (err) {
                alert("Error adding employee: " + err.message);
            }
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this employee?")) {
            try {
                await axios.delete(`http://localhost:5001/api/employees/${id}`);
                fetchEmployees();
            } catch (err) {
                alert("Error deleting employee");
            }
        }
    };

    const openEditModal = (emp) => {
        setFormData({
            name: emp.name,
            employee_id: emp.employee_id,
            department: emp.department,
            designation: emp.designation,
            email: emp.email,
            file: null // File update not supported in simple edit for now
        });
        setCurrentId(emp.id);
        setIsEditing(true);
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setIsEditing(false);
        setCurrentId(null);
        setFormData({
            name: '',
            employee_id: '',
            department: '',
            designation: '',
            email: '',
            file: null
        });
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Employee Management</h1>
                    <p className="text-gray-400">Manage your workforce database.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-neon-blue hover:bg-neon-blue/80 text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-[0_0_15px_rgba(0,243,255,0.3)]"
                >
                    <Plus size={20} />
                    Add Employee
                </button>
            </div>

            {/* Employee List */}
            <div className="glass-panel overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-white/5 text-gray-400 text-sm uppercase tracking-wider">
                        <tr>
                            <th className="p-4">Employee</th>
                            <th className="p-4">ID</th>
                            <th className="p-4">Department</th>
                            <th className="p-4">Designation</th>
                            <th className="p-4">Employment Status</th>
                            <th className="p-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-border text-gray-300">
                        {employees.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="p-8 text-center text-gray-500">No employees found.</td>
                            </tr>
                        ) : (
                            employees.map((emp) => (
                                <tr key={emp.id} className="hover:bg-white/5 transition-colors">
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-white">
                                                {emp.name.substring(0, 2).toUpperCase()}
                                            </div>
                                            <div>
                                                <p className="font-medium text-white">{emp.name}</p>
                                                <p className="text-xs text-gray-500">{emp.email}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">{emp.employee_id}</td>
                                    <td className="p-4">{emp.department}</td>
                                    <td className="p-4">{emp.designation}</td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                                            Employed
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button onClick={() => openEditModal(emp)} className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                                                <Edit2 size={16} />
                                            </button>
                                            <button onClick={() => handleDelete(emp.id)} className="p-2 hover:bg-red-500/10 rounded-lg text-gray-400 hover:text-red-400 transition-colors">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
                    <div className="glass-panel w-full max-w-lg p-6 relative">
                        <button onClick={closeModal} className="absolute top-4 right-4 text-gray-400 hover:text-white">
                            <X size={24} />
                        </button>
                        <h2 className="text-2xl font-bold text-white mb-6">{isEditing ? 'Edit Employee' : 'Add New Employee'}</h2>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <input
                                    name="name" value={formData.name} onChange={handleInputChange}
                                    type="text" placeholder="Full Name" required
                                    className="bg-dark-bg border border-dark-border rounded-lg p-3 text-white w-full"
                                />
                                <input
                                    name="employee_id" value={formData.employee_id} onChange={handleInputChange}
                                    type="text" placeholder="Employee ID" required
                                    className="bg-dark-bg border border-dark-border rounded-lg p-3 text-white w-full"
                                />
                            </div>
                            <input
                                name="email" value={formData.email} onChange={handleInputChange}
                                type="email" placeholder="Email" required
                                className="bg-dark-bg border border-dark-border rounded-lg p-3 text-white w-full"
                            />
                            <div className="grid grid-cols-2 gap-4">
                                <input
                                    name="department" value={formData.department} onChange={handleInputChange}
                                    type="text" placeholder="Department" required
                                    className="bg-dark-bg border border-dark-border rounded-lg p-3 text-white w-full"
                                />
                                <input
                                    name="designation" value={formData.designation} onChange={handleInputChange}
                                    type="text" placeholder="Designation" required
                                    className="bg-dark-bg border border-dark-border rounded-lg p-3 text-white w-full"
                                />
                            </div>

                            {!isEditing && (
                                <div className="border-2 border-dashed border-dark-border rounded-lg p-6 text-center hover:border-neon-blue transition-colors relative">
                                    <input
                                        type="file" accept="image/*" onChange={handleFileChange}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    />
                                    <p className="text-gray-400">{formData.file ? formData.file.name : "Click to upload face photo"}</p>
                                    <p className="text-xs text-gray-600 mt-2">Required for recognition</p>
                                </div>
                            )}

                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={closeModal} className="px-4 py-2 text-gray-400 hover:text-white">Cancel</button>
                                <button type="submit" className="bg-neon-blue text-black font-bold px-6 py-2 rounded-lg flex items-center gap-2">
                                    <Save size={18} />
                                    {isEditing ? 'Update' : 'Save'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Employees;
