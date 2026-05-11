import React, { useState, useEffect } from 'react'

export default function UsersPanel() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/admin/users/?per_page=100')
      .then(res => res.json())
      .then(res => {
        setUsers(res.data)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="p-10 text-center text-aras-primary/50 italic">Loading users...</div>

  return (
    <div className="animate-fade-in space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">User Directory</h3>
          <p className="text-aras-primary/50 text-sm italic">Manage system access and authentication profiles.</p>
        </div>
        <button className="bg-aras-accent text-white px-6 py-2 text-[10px] font-bold uppercase tracking-widest hover:bg-aras-accent/90 transition-all shadow-lg shadow-aras-accent/20">
          Create New User
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {users.map(user => (
          <div key={user.id} className="bg-white border border-aras-primary/10 p-6 shadow-sm group hover:border-aras-accent/30 transition-all hover:shadow-md">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-aras-primary/5 rounded-full flex items-center justify-center text-aras-primary/20 text-xl font-bold border border-aras-primary/10 group-hover:bg-aras-accent/5 group-hover:text-aras-accent/30 transition-all">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div>
                <h4 className="font-bold text-aras-primary text-sm">{user.username}</h4>
                <p className="text-[10px] text-aras-primary/40 truncate w-32">{user.email}</p>
              </div>
              <div className="ml-auto">
                 <span className={`w-2 h-2 rounded-full block ${user.is_active ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              </div>
            </div>
            
            <div className="space-y-2 pt-4 border-t border-aras-primary/5">
               <div className="flex justify-between text-[9px] uppercase font-bold tracking-wider">
                  <span className="text-aras-primary/30">Last Login</span>
                  <span className="text-aras-primary/60">{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</span>
               </div>
               <div className="flex justify-between text-[9px] uppercase font-bold tracking-wider">
                  <span className="text-aras-primary/30">Role</span>
                  <span className="text-aras-accent">Administrator</span>
               </div>
            </div>

            <div className="mt-6 flex gap-2">
               <button className="flex-1 bg-aras-primary/5 text-aras-primary/60 py-2 text-[9px] font-bold uppercase tracking-widest hover:bg-aras-primary hover:text-white transition-all">Settings</button>
               <button className="px-3 bg-aras-primary/5 text-aras-primary/60 py-2 text-[9px] font-bold uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all">
                  <i className="fa fa-trash"></i>
               </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
