import React from 'react'
import { Link } from 'react-router-dom'

export default function ArasSidebar({ menu, currentApp }) {
  const dashboard = menu.find(m => m.slug === 'dashboard')
  const apps = menu.filter(m => m.source === 'db' || m.source === 'manifest')
  const system = menu.filter(m => m.slug === 'admin' || m.slug === 'trash')

  const NavItem = ({ item }) => (
    <Link 
      to={item.url}
      className={`flex items-center px-3 py-2 text-xs font-medium transition-all duration-200 group ${
        currentApp === item.slug
          ? 'text-white bg-white/10 border-l-2 border-aras-accent pl-[10px]' 
          : 'text-white/60 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
      }`}
    >
      <i className={`fa ${item.icon || 'fa-cubes'} w-4 text-center opacity-50 group-hover:opacity-100 transition-opacity mr-3`}></i>
      <span>{item.title}</span>
    </Link>
  )

  return (
    <aside className="w-[240px] bg-aras-primary border-r border-white/10 flex-shrink-0 flex flex-col z-30 overflow-y-auto">
      {/* BRAND / LOGO */}
