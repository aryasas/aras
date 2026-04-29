/**
 * Aras Design System - UI Tweaks
 * Handles Theme, Density, Corners and Accent color.
 */

(function() {
    "use strict";

    var ArasTweaks = {
        storageKey: 'aras_ui_tweaks',
        defaults: {
            theme: 'light',
            density: 'cozy',
            corners: 'sharp',
            accent: 'terra'
        },

        init: function() {
            this.loadSettings();
            this.bindEvents();
            this.syncUI();
        },

        loadSettings: function() {
            var saved = localStorage.getItem(this.storageKey);
            this.settings = saved ? JSON.parse(saved) : Object.assign({}, this.defaults);
            this.applySettings();
        },

        applySettings: function() {
            var root = document.documentElement;
            var s = this.settings;
            
            root.dataset.theme = s.theme;
            root.dataset.density = s.density;
            root.dataset.corners = s.corners;
            
            // Apply accent color
            var accentColors = {
                terra: '#b08968',
                moss: '#82947d',
                wheat: '#d2b48c',
                slate: '#708090',
                plum: '#8e44ad',
                rose: '#e91e63'
            };
            
            if (accentColors[s.accent]) {
                root.style.setProperty('--aras-accent', accentColors[s.accent]);
            }
        },

        saveSettings: function() {
            localStorage.setItem(this.storageKey, JSON.stringify(this.settings));
        },

        bindEvents: function() {
            var self = this;
            var toggle = document.getElementById('twToggle');
            var panel = document.getElementById('twPanel');
            var close = document.getElementById('twClose');

            if (toggle && panel) {
                toggle.addEventListener('click', function() {
                    panel.classList.toggle('is-open');
                });
            }

            if (close && panel) {
                close.addEventListener('click', function() {
                    panel.classList.remove('is-open');
                });
            }

            // Segmented buttons
            document.querySelectorAll('.tw-row .seg button').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var key = this.parentElement.dataset.key;
                    var val = this.dataset.val;
                    
                    self.settings[key] = val;
                    self.applySettings();
                    self.saveSettings();
                    self.syncUI();
                });
            });

            // Swatches
            document.querySelectorAll('.tw-row .swatches button').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var key = this.parentElement.dataset.key;
                    var val = this.dataset.val;
                    
                    self.settings[key] = val;
                    self.applySettings();
                    self.saveSettings();
                    self.syncUI();
                });
            });
        },

        syncUI: function() {
            var self = this;
            // Update segmented buttons
            document.querySelectorAll('.tw-row .seg button').forEach(function(btn) {
                var key = btn.parentElement.dataset.key;
                var val = btn.dataset.val;
                if (self.settings[key] === val) {
                    btn.classList.add('on');
                } else {
                    btn.classList.remove('on');
                }
            });

            // Update swatches
            document.querySelectorAll('.tw-row .swatches button').forEach(function(btn) {
                var key = btn.parentElement.dataset.key;
                var val = btn.dataset.val;
                if (self.settings[key] === val) {
                    btn.classList.add('on');
                } else {
                    btn.classList.remove('on');
                }
            });
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { ArasTweaks.init(); });
    } else {
        ArasTweaks.init();
    }
})();
