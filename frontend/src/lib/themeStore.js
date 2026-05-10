import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useThemeStore = create(
  persist(
    (set, get) => ({
      // CORE COLORS
      primaryColor: '#0f1b2d', // Dark Ink
      accentColor: '#c9a568',  // Ochre
      errorColor: '#6b2c2c',   // Oxblood
      backgroundColor: '#faf8f3', // Ivory

      // STYLING
      fontFamily: 'sans', // 'sans' | 'serif' | 'mono'
      borderRadius: '6px', // '0px' | '4px' | '8px' | '16px'
      buttonStyle: 'flat', // 'flat' | 'outline' | 'glass'
      
      // DENSITY
      density: 'regular', // 'compact' | 'regular' | 'comfy'
      
      // DERIVED ACTIONS
      setTheme: (key, value) => set({ [key]: value }),
      
      resetTheme: () => set({
        primaryColor: '#0f1b2d',
        accentColor: '#c9a568',
        errorColor: '#6b2c2c',
        backgroundColor: '#faf8f3',
        fontFamily: 'sans',
        borderRadius: '6px',
        buttonStyle: 'flat',
        density: 'regular'
      }),

      applyToDOM: () => {
        const state = get()
        const root = document.documentElement
        
        // Colors
        root.style.setProperty('--aras-primary', state.primaryColor)
        root.style.setProperty('--aras-accent', state.accentColor)
        root.style.setProperty('--aras-error', state.errorColor)
        root.style.setProperty('--aras-bg', state.backgroundColor)
        
        // Radius
        root.style.setProperty('--aras-radius', state.borderRadius)
        
        // Density mapping
        const paddingMap = {
          compact: '0.5rem',
          regular: '1rem',
          comfy: '1.5rem'
        }
        root.style.setProperty('--aras-spacing', paddingMap[state.density])
        
        // Font mapping
        const fontMap = {
          sans: "'Bricolage Grotesque', sans-serif",
          serif: "'Libre Baskerville', serif",
          mono: "'JetBrains Mono', monospace"
        }
        root.style.setProperty('--aras-font-main', fontMap[state.fontFamily])
        
        // Global Classes
        if (state.borderRadius === '0px') {
          root.classList.add('aras-square-mode')
        } else {
          root.classList.remove('aras-square-mode')
        }
      }
    }),
    {
      name: 'aras-theme-storage',
    }
  )
)
