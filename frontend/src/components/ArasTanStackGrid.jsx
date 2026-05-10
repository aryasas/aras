import React from 'react'
import { flexRender } from '@tanstack/react-table'

export default function ArasTanStackGrid({ table, isLoading, onRowClick }) {
  return (
    <div className="flex-1 overflow-auto relative bg-white border border-[#dde3e7] rounded-none shadow-sm">
      <table className="w-full border-collapse text-left" style={{ tableLayout: 'fixed' }}>
        <thead className="sticky top-0 z-20 bg-[#f4f2ee] border-b border-[#dde3e7]">
          {table.getHeaderGroups().map(headerGroup => (
...
        </thead>
        <tbody className="divide-y divide-[#f0f3f5]">
          {table.getRowModel().rows.map(row => (
            <tr 
              key={row.id} 
              onClick={() => onRowClick && onRowClick(row)}
              className={`transition-colors group ${onRowClick ? 'cursor-pointer hover:bg-[#fbfcfd]' : 'hover:bg-[#fbfcfd]'}`}
            >
              {row.getVisibleCells().map(cell => (
                <td 
                  key={cell.id} 
                  className="px-6 py-4 text-sm text-[#313b3d] whitespace-nowrap overflow-hidden text-ellipsis font-medium"
