import React, { useState, useEffect } from 'react'
import { useThemeStore } from '../lib/themeStore'

export const TweakPanel = () => {
  const [isOpen, setIsOpen] = useState(false)
  const theme = useThemeStore()

  useEffect(() => {
    theme.applyToDOM()
  }, [theme])

  const ColorCircle = ({ label, value, stateKey }) => (
    <div className="flex items-center justify-between group">
      <span className="text-[10px] uppercase font-bold text-[#9aacb8] tracking-widest">{label}</span>
      <div className="flex items-center gap-3">
        <span className="text-[10px] font-mono text-[#0f1b2d] opacity-0 group-hover:opacity-100 transition-opacity">{value}</span>
        <input 
          type="color" 
          value={value} 
          onChange={(e) => theme.setTheme(stateKey, e.target.value)}
          className="w-6 h-6 rounded-full overflow-hidden border-2 border-white shadow-sm cursor-pointer"
        />
      </div>
    </div>
  )

  const ToggleBtn = ({ label, value, options, stateKey }) => (
    <div className="space-y-2">
      <span className="text-[10px] uppercase font-bold text-[#9aacb8] tracking-widest block">{label}</span>
      <div className="grid grid-cols-3 gap-1 bg-[#f0f2f4] p-1 rounded-md">
        {options.map(opt => (
          <button
            key={opt.value}
            onClick={() => theme.setTheme(stateKey, opt.value)}
            className={`px-2 py-1.5 text-[9px] font-bold uppercase rounded transition-all ${
              value === opt.value 
              ? 'bg-white text-[#0f1b2d] shadow-sm' 
              : 'text-[#9aacb8] hover:text-[#0f1b2d]'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )

  return (
    <>
      {/* TRIGGER */}
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-8 right-8 w-12 h-12 bg-[#0f1b2d] text-white rounded-full shadow-2xl flex items-center justify-center z-[100] hover:scale-110 active:scale-95 transition-all group"
      >
        <svg className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>

      {/* PANEL */}
      <div className={`fixed inset-y-0 right-0 w-80 bg-white shadow-[-20px_0_50px_rgba(0,0,0,0.1)] z-[101] transform transition-transform duration-500 ease-in-out border-l border-[#dde3e7] ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="h-full flex flex-col">
          {/* HEADER */}
          <div className="p-6 border-b border-[#eef0f2] flex items-center justify-between bg-[#faf8f3]">
            <div>
              <h3 className="font-studio-serif font-bold text-[#0f1b2d]">Aesthetic Tweaks</h3>
              <p className="text-[10px] text-[#9aacb8] font-bold uppercase tracking-widest mt-1">Real-time Customization</p>
            </div>
            <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-[#eef0f2] rounded-full transition-colors">
              <svg className="w-5 h-5 text-[#9aacb8]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l18 18" />
              </svg>
            </button>
          </div>

          {/* BODY */}
          <div className="flex-1 overflow-y-auto p-6 space-y-10">
            {/* COLORS */}
            <div className="space-y-4">
              <h4 className="text-[11px] font-bold text-[#0f1b2d] uppercase tracking-[0.2em] border-b border-[#eef0f2] pb-2">Palette</h4>
              <ColorCircle label="Primary" value={theme.primaryColor} stateKey="primaryColor" />
              <ColorCircle label="Accent" value={theme.accentColor} stateKey="accentColor" />
              <ColorCircle label="Background" value={theme.backgroundColor} stateKey="backgroundColor" />
              <ColorCircle label="Validation" value={theme.errorColor} stateKey="errorColor" />
            </div>

            {/* TYPOGRAPHY */}
            <ToggleBtn 
              label="Typeface" 
              value={theme.fontFamily} 
              stateKey="fontFamily"
              options={[
                { label: 'Grotesque', value: 'sans' },
                { label: 'Baskerville', value: 'serif' },
                { label: 'Mono', value: 'mono' }
              ]}
            />

            {/* RADIUS */}
            <ToggleBtn 
              label="Edge Sharpness" 
              value={theme.borderRadius} 
              stateKey="borderRadius"
              options={[
                { label: 'Square', value: '0px' },
                { label: 'Soft', value: '8px' },
                { label: 'Round', value: '24px' }
              ]}
            />

            {/* DENSITY */}
            <ToggleBtn 
              label="Layout Density" 
              value={theme.density} 
              stateKey="density"
              options={[
                { label: 'Compact', value: 'compact' },
                { label: 'Regular', value: 'regular' },
                { label: 'Comfy', value: 'comfy' }
              ]}
            />
          </div>

          {/* FOOTER */}
          <div className="p-6 bg-[#faf8f3] border-t border-[#eef0f2] flex gap-3">
            <button 
              onClick={theme.resetTheme}
              className="flex-1 px-4 py-2 border border-[#dde3e7] text-[#9aacb8] text-[10px] font-bold uppercase tracking-widest rounded hover:bg-white transition-colors"
            >
              Reset
            </button>
            <button 
              onClick={() => setIsOpen(false)}
              className="flex-1 px-4 py-2 bg-[#0f1b2d] text-white text-[10px] font-bold uppercase tracking-widest rounded hover:opacity-90 transition-opacity"
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* OVERLAY */}
      {isOpen && (
        <div 
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 bg-black/5 backdrop-blur-[2px] z-[99] transition-opacity"
        />
      )}
    </>
  )
}
