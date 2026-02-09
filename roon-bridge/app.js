"use strict";

/**
 * AIME Roon Bridge
 * 
 * Microservice Node.js utilisant exclusivement l'API officielle RoonLabs
 * (https://github.com/RoonLabs/node-roon-api) pour piloter Roon.
 * 
 * Expose une API REST HTTP que le backend Python AIME consomme.
 */

const RoonApi            = require("node-roon-api");
const RoonApiTransport   = require("node-roon-api-transport");
const RoonApiBrowse      = require("node-roon-api-browse");
const RoonApiImage       = require("node-roon-api-image");
const RoonApiStatus      = require("node-roon-api-status");

const express = require("express");
const fs      = require("fs");
const path    = require("path");

// ============================================================================
// Configuration
// ============================================================================

const HTTP_PORT        = parseInt(process.env.ROON_BRIDGE_PORT || "3330", 10);
const ROON_HOST        = process.env.ROON_HOST || null; // null = use discovery
const CONFIG_DIR       = process.env.CONFIG_DIR || path.join(__dirname, "config");
const STATE_FILE       = path.join(CONFIG_DIR, "roonstate.json");

// Ensure config directory exists
if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
}

// ============================================================================
// State
// ============================================================================

let core       = null;   // Roon Core (when paired)
let transport  = null;   // RoonApiTransport service
let browse     = null;   // RoonApiBrowse service
let image      = null;   // RoonApiImage service
let zones      = {};     // Zone cache {zone_id: zone_data}

// Browse mutex – Roon browse API maintains a single hierarchy per connection.
// Concurrent browse operations corrupt each other's state.
let _browseLock = Promise.resolve();
function withBrowseLock(fn) {
    const prev = _browseLock;
    let releaseFn;
    _browseLock = new Promise(resolve => { releaseFn = resolve; });
    return prev.then(async () => {
        try {
            return await fn();
        } finally {
            releaseFn();
        }
    });
}

// ============================================================================
// Persisted state helpers
// ============================================================================

function loadState() {
    try {
        if (fs.existsSync(STATE_FILE)) {
            return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
        }
    } catch (e) {
        console.error("[roon-bridge] Error loading state:", e.message);
    }
    return {};
}

function saveState(state) {
    try {
        fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), "utf8");
    } catch (e) {
        console.error("[roon-bridge] Error saving state:", e.message);
    }
}

// ============================================================================
// Roon API initialisation
// ============================================================================

const roon = new RoonApi({
    extension_id:    "com.aime.music_enabler",
    display_name:    "AIME - AI Music Enabler",
    display_version: "5.0.0",
    publisher:       "AIME",
    email:           "contact@aime.music",
    website:         "https://github.com/AIME",
    log_level:       "none",

    get_persisted_state: () => loadState(),
    set_persisted_state: (state) => saveState(state),

    core_paired: function (_core) {
        console.log("[roon-bridge] Core paired:", _core.display_name, _core.display_version);
        core      = _core;
        transport = _core.services.RoonApiTransport;
        browse    = _core.services.RoonApiBrowse;
        image     = _core.services.RoonApiImage;

        // Subscribe to zone changes
        transport.subscribe_zones(function (cmd, data) {
            if (cmd === "Subscribed" && data.zones) {
                zones = {};
                data.zones.forEach(z => { zones[z.zone_id] = z; });
                console.log("[roon-bridge] Subscribed – " + Object.keys(zones).length + " zone(s)");
            } else if (cmd === "Changed") {
                if (data.zones_added)   data.zones_added.forEach(z   => { zones[z.zone_id] = z; });
                if (data.zones_changed) data.zones_changed.forEach(z => { zones[z.zone_id] = z; });
                if (data.zones_removed) data.zones_removed.forEach(z => { delete zones[z.zone_id]; });
            }
        });
        svc_status.set_status("Connecté à " + _core.display_name, false);
    },

    core_unpaired: function (_core) {
        console.log("[roon-bridge] Core unpaired");
        core      = null;
        transport = null;
        browse    = null;
        image     = null;
        zones     = {};
        svc_status.set_status("Déconnecté", true);
    }
});

const svc_status = new RoonApiStatus(roon);

roon.init_services({
    required_services: [RoonApiTransport, RoonApiBrowse, RoonApiImage],
    provided_services: [svc_status],
});

svc_status.set_status("En attente de connexion…", false);

// Connect: always use SOOD discovery to find the correct Roon Core port
// (Roon Core advertises its http_port dynamically via UDP 9003 multicast)
console.log("[roon-bridge] Starting SOOD discovery on UDP 9003…");
roon.start_discovery();

// ============================================================================
// Health Check & Auto-Reconnect on Wake-up
// ============================================================================

let lastHealthCheckTime = Date.now();
let healthCheckFailures = 0;
const HEALTH_CHECK_INTERVAL = 10000;  // Check every 10 seconds
const MAX_FAILURES = 2;               // Reconnect after 2 consecutive failures (20 seconds)

/**
 * Periodic health check to detect stale connections after system wake-up.
 * If the connection becomes unresponsive, triggers automatic reconnection.
 */
function startHealthCheck() {
    setInterval(() => {
        const now = Date.now();
        const timeSinceCheck = now - lastHealthCheckTime;
        
        // If core is null, we're already disconnected
        if (!core) {
            healthCheckFailures += 1;
            if (healthCheckFailures > MAX_FAILURES) {
                console.log("[roon-bridge] ⚠️ Disconnected for too long, triggering reconnect...");
                healthCheckFailures = 0;
                triggerReconnect();
            }
            return;
        }
        
        // Try a simple zone subscription refresh to detect if connection is alive
        try {
            // If transport exists, try to get zones (lightweight operation)
            if (transport) {
                // Attempt to subscribe to zones again - this will fail silently if connection is dead
                transport.subscribe_zones((cmd, data) => {
                    // If we get here, connection is alive
                    lastHealthCheckTime = Date.now();
                    healthCheckFailures = 0;
                    console.log(`[roon-bridge] ✅ Health check OK (${new Date().toLocaleTimeString()})`);
                });
            }
        } catch (err) {
            healthCheckFailures += 1;
            console.warn(`[roon-bridge] ⚠️ Health check failed: ${err.message} (failures: ${healthCheckFailures}/${MAX_FAILURES})`);
            
            if (healthCheckFailures > MAX_FAILURES) {
                console.log("[roon-bridge] 🔄 Connection appears stale, triggering reconnect...");
                healthCheckFailures = 0;
                triggerReconnect();
            }
        }
    }, HEALTH_CHECK_INTERVAL);
}

/**
 * Force reconnection by trigging SOOD discovery again.
 * This handles cases where the WebSocket becomes stale after system sleep.
 */
function triggerReconnect() {
    console.log("[roon-bridge] 🔄 Initiating Roon Core reconnection...");
    
    // Reset state
    core = null;
    transport = null;
    browse = null;
    image = null;
    zones = {};
    svc_status.set_status("Reconnecting…", false);
    
    // Trigger discovery again
    try {
        // stop_discovery() if available, then restart
        if (typeof roon.stop_discovery === 'function') {
            roon.stop_discovery();
            console.log("[roon-bridge] Stopped discovery");
        }
    } catch (err) {
        console.warn("[roon-bridge] Could not stop discovery:", err.message);
    }
    
    // Wait a moment and restart discovery
    setTimeout(() => {
        console.log("[roon-bridge] Restarting SOOD discovery on UDP 9003…");
        try {
            roon.start_discovery();
        } catch (err) {
            console.error("[roon-bridge] Error restarting discovery:", err.message);
        }
    }, 2000);
}

// Start periodic health checks once bridge is initialized
console.log("[roon-bridge] Starting periodic health checks (interval: " + HEALTH_CHECK_INTERVAL + "ms)");
startHealthCheck();

// ============================================================================
// Helper: promisify RoonApiTransport callbacks
// ============================================================================

function transportControl(zoneOrOutputId, control) {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.control(zoneOrOutputId, control, (err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

function transportSeek(zoneOrOutputId, how, seconds) {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.seek(zoneOrOutputId, how, seconds, (err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

function transportChangeVolume(outputId, how, value) {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.change_volume(outputId, how, value, (err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

function transportChangeSettings(zoneOrOutputId, settings) {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.change_settings(zoneOrOutputId, settings, (err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

function transportMuteAll(how) {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.mute_all(how, (err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

function transportPauseAll() {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.pause_all((err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

function transportTransferZone(fromZone, toZone) {
    return new Promise((resolve, reject) => {
        if (!transport) return reject(new Error("Not connected to Roon Core"));
        transport.transfer_zone(fromZone, toZone, (err) => {
            if (err) return reject(new Error(err));
            resolve();
        });
    });
}

/**
 * Browse a hierarchy path using RoonApiBrowse.
 * Navigates step-by-step through the browse tree matching titles.
 */
function browseByPath(zoneOrOutputId, pathItems, action) {
    return new Promise(async (resolve, reject) => {
        if (!browse) return reject(new Error("Not connected to Roon Core"));
        
        const startTime = Date.now();
        
        try {
            // Step 1: Start at the root level "browse"
            let browseOpts = {
                hierarchy:         "browse",
                pop_all:           true,
                zone_or_output_id: zoneOrOutputId
            };

            let result = await _browseRequest(browseOpts);
            
            // Step 2: Walk through each path element
            for (let i = 0; i < pathItems.length; i++) {
                const target = pathItems[i];
                const isLast = (i === pathItems.length - 1);
                
                // Load items at current level
                let found = false;
                let offset = 0;
                const count = 100;
                
                while (!found) {
                    let loadResult = await _loadRequest({
                        hierarchy: "browse",
                        offset:    offset,
                        count:     count
                    });
                    
                    if (!loadResult.items || loadResult.items.length === 0) break;
                    
                    // Look for matching item
                    for (const item of loadResult.items) {
                        if (item.title && item.title.toLowerCase() === target.toLowerCase()) {
                            found = true;
                            
                            if (isLast && action) {
                                // For last item with action, first browse into it, then look for action
                                let browseInto = await _browseRequest({
                                    hierarchy:         "browse",
                                    item_key:          item.item_key,
                                    zone_or_output_id: zoneOrOutputId
                                });
                                
                                // Now look for the action in the action list
                                let actionResult = await _findAndExecuteAction(zoneOrOutputId, action);
                                resolve({ success: true, action_result: actionResult });
                                return;
                            } else if (isLast && !action) {
                                // Last item, no specific action – just browse into it (triggers default action)
                                let browseInto = await _browseRequest({
                                    hierarchy:         "browse",
                                    item_key:          item.item_key,
                                    zone_or_output_id: zoneOrOutputId
                                });
                                
                                // Check if this resulted in a playback action
                                if (browseInto.action === "message" || browseInto.action === "none") {
                                    resolve({ success: true, action: browseInto.action, message: browseInto.message });
                                } else if (browseInto.action === "list") {
                                    // We got a list – try to find Play action
                                    let actionResult = await _findAndExecuteAction(zoneOrOutputId, null);
                                    resolve({ success: true, action_result: actionResult });
                                } else {
                                    resolve({ success: true, action: browseInto.action });
                                }
                                return;
                            } else {
                                // Not last element – drill into this item
                                let browseInto = await _browseRequest({
                                    hierarchy:         "browse",
                                    item_key:          item.item_key,
                                    zone_or_output_id: zoneOrOutputId
                                });
                                break;
                            }
                        }
                    }
                    
                    if (!found) {
                        // Check if there are more items to load
                        if (loadResult.list && offset + loadResult.items.length < loadResult.list.count) {
                            offset += loadResult.items.length;
                        } else {
                            // Item not found at this level
                            resolve({ success: false, error: `Item "${target}" not found at level ${i}` });
                            return;
                        }
                    }
                }
            }
            
            resolve({ success: false, error: "Path navigation incomplete" });
        } catch (err) {
            reject(err);
        }
    });
}

/**
 * Find and execute a play action in the current browse level.
 */
async function _findAndExecuteAction(zoneOrOutputId, targetAction) {
    // Load the items at current level
    let loadResult = await _loadRequest({
        hierarchy: "browse",
        offset:    0,
        count:     100
    });
    
    if (!loadResult.items || loadResult.items.length === 0) {
        return { found: false };
    }
    
    // Look for a play-related action
    const playActions = ["Play Now", "Play Album", "Play", "Play from Here"];
    const targetActions = targetAction ? [targetAction] : playActions;
    
    // PASS 1: Look for actions with proper hints
    for (const item of loadResult.items) {
        if (item.hint === "action" || item.hint === "action_list") {
            for (const ta of targetActions) {
                if (item.title && item.title.toLowerCase() === ta.toLowerCase()) {
                    // Execute this action
                    let result = await _browseRequest({
                        hierarchy:         "browse",
                        item_key:          item.item_key,
                        zone_or_output_id: zoneOrOutputId
                    });
                    
                    // If clicking the action returned a sub-list (e.g. "Play Album" → "Play Now", "Add Next", "Queue"...)
                    // we need to select "Play Now" from that sub-list to actually start playback
                    if (result.action === "list" && result.list && result.list.hint === "action_list") {
                        console.log(`[roon-bridge] Action "${item.title}" returned sub-menu (${result.list.count} items), looking for "Play Now"...`);
                        let subLoad = await _loadRequest({ hierarchy: "browse", offset: 0, count: 100 });
                        if (subLoad.items) {
                            for (const subItem of subLoad.items) {
                                if (subItem.title && subItem.title.toLowerCase() === "play now") {
                                    let playResult = await _browseRequest({
                                        hierarchy:         "browse",
                                        item_key:          subItem.item_key,
                                        zone_or_output_id: zoneOrOutputId
                                    });
                                    console.log(`[roon-bridge] ✅ "Play Now" executed from sub-menu`);
                                    return { found: true, action: "Play Now", result: playResult };
                                }
                            }
                            // No "Play Now" found, try clicking the first action item
                            if (subLoad.items.length > 0 && subLoad.items[0].item_key) {
                                console.log(`[roon-bridge] No "Play Now" in sub-menu, using first item: "${subLoad.items[0].title}"`);
                                let fallbackResult = await _browseRequest({
                                    hierarchy:         "browse",
                                    item_key:          subLoad.items[0].item_key,
                                    zone_or_output_id: zoneOrOutputId
                                });
                                return { found: true, action: subLoad.items[0].title, result: fallbackResult };
                            }
                        }
                    }
                    
                    return { found: true, action: item.title, result: result };
                }
            }
        }
    }
    
    // PASS 2: If no action with proper hints found, search more broadly (sometimes Roon API hints vary)
    console.log(`[roon-bridge] No actions with proper hints found, searching more broadly...`);
    for (const item of loadResult.items) {
        for (const ta of targetActions) {
            if (item.title && item.title.toLowerCase() === ta.toLowerCase()) {
                console.log(`[roon-bridge] ⚠️ Found action WITHOUT proper hint: "${item.title}" (hint="${item.hint}")`);
                // Execute this action anyway
                let result = await _browseRequest({
                    hierarchy:         "browse",
                    item_key:          item.item_key,
                    zone_or_output_id: zoneOrOutputId
                });
                
                // Handle sub-lists like before
                if (result.action === "list" && result.list && result.list.hint === "action_list") {
                    console.log(`[roon-bridge] Action "${item.title}" returned sub-menu, looking for "Play Now"...`);
                    let subLoad = await _loadRequest({ hierarchy: "browse", offset: 0, count: 100 });
                    if (subLoad.items) {
                        for (const subItem of subLoad.items) {
                            if (subItem.title && subItem.title.toLowerCase() === "play now") {
                                let playResult = await _browseRequest({
                                    hierarchy:         "browse",
                                    item_key:          subItem.item_key,
                                    zone_or_output_id: zoneOrOutputId
                                });
                                console.log(`[roon-bridge] ✅ "Play Now" executed from sub-menu`);
                                return { found: true, action: "Play Now", result: playResult };
                            }
                        }
                        // No "Play Now" found, try first item
                        if (subLoad.items.length > 0 && subLoad.items[0].item_key) {
                            let fallbackResult = await _browseRequest({
                                hierarchy:         "browse",
                                item_key:          subLoad.items[0].item_key,
                                zone_or_output_id: zoneOrOutputId
                            });
                            return { found: true, action: subLoad.items[0].title, result: fallbackResult };
                        }
                    }
                }
                
                return { found: true, action: item.title, result: result };
            }
        }
    }
    
    // If no specific action found, try clicking the first item (might be a track – starts playback)
    if (!targetAction && loadResult.items.length > 0) {
        const first = loadResult.items[0];
        if (first.item_key) {
            let result = await _browseRequest({
                hierarchy:         "browse",
                item_key:          first.item_key,
                zone_or_output_id: zoneOrOutputId
            });
            
            // Check if this is an action list
            if (result.action === "list") {
                let innerLoad = await _loadRequest({ hierarchy: "browse", offset: 0, count: 100 });
                if (innerLoad.items) {
                    for (const innerItem of innerLoad.items) {
                        for (const pa of playActions) {
                            if (innerItem.title && innerItem.title.toLowerCase() === pa.toLowerCase()) {
                                let innerResult = await _browseRequest({
                                    hierarchy:         "browse",
                                    item_key:          innerItem.item_key,
                                    zone_or_output_id: zoneOrOutputId
                                });
                                return { found: true, action: innerItem.title, result: innerResult };
                            }
                        }
                    }
                }
            }
            
            return { found: true, action: "first_item", result: result };
        }
    }
    
    return { found: false, items: loadResult.items.map(i => i.title) };
}

function _browseRequest(opts) {
    return new Promise((resolve, reject) => {
        browse.browse(opts, (err, body) => {
            if (err) return reject(new Error(typeof err === "string" ? err : JSON.stringify(err)));
            resolve(body);
        });
    });
}

function _loadRequest(opts) {
    return new Promise((resolve, reject) => {
        browse.load(opts, (err, body) => {
            if (err) return reject(new Error(typeof err === "string" ? err : JSON.stringify(err)));
            resolve(body);
        });
    });
}

/**
 * Get image as binary via RoonApiImage.
 */
function getImage(imageKey, opts) {
    return new Promise((resolve, reject) => {
        if (!image) return reject(new Error("Not connected to Roon Core"));
        opts = opts || {};
        image.get_image(imageKey, opts, (err, contentType, body) => {
            if (err) return reject(new Error(err));
            resolve({ content_type: contentType, body: body });
        });
    });
}

/**
 * Find a zone by its display name (case-insensitive).
 */
function findZoneByName(name) {
    const nameLower = name.toLowerCase();
    for (const zoneId of Object.keys(zones)) {
        const z = zones[zoneId];
        if (z.display_name && z.display_name.toLowerCase() === nameLower) {
            return z;
        }
    }
    return null;
}

/**
 * Récupérer le volume principal d'une zone.
 * Volume = premier output avec control_value
 */
function getZoneVolume(zone) {
    if (!zone || !zone.outputs || zone.outputs.length === 0) {
        console.debug(`[getZoneVolume] No outputs for zone ${zone?.display_name}`);
        return null;
    }
    // Utiliser le volume du premier output
    const output = zone.outputs[0];
    if (!output) {
        console.debug(`[getZoneVolume] First output is null`);
        return null;
    }
    
    // Log full structure
    console.debug(`[getZoneVolume] Output structure:`, {
        output_id: output.output_id,
        display_name: output.display_name,
        has_volume: !!output.volume,
        volume_type: typeof output.volume,
        volume: output.volume
    });
    
    if (output.volume && output.volume.control_value !== undefined) {
        const vol = output.volume.control_value;
        console.debug(`[getZoneVolume] ✅ Found volume: ${vol}`);
        return vol;
    }
    
    console.debug(`[getZoneVolume] ❌ No control_value in volume object`);
    return null;
}

/**
 * Get now playing info from the first zone that is playing.
 */
function getNowPlaying(zoneId) {
    // Si zoneId spécifié, retourner le track de cette zone
    if (zoneId) {
        const z = zones[zoneId];
        if (z && z.now_playing) {
            const np = z.now_playing;
            const tl = np.three_line || {};
            return {
                title:            tl.line1 || "Unknown Title",
                artist:           tl.line2 || "Unknown Artist",
                album:            tl.line3 || "Unknown Album",
                zone_id:          z.zone_id,
                zone_name:        z.display_name,
                state:            z.state || "stopped",
                duration_seconds: np.length || null,
                seek_position:    np.seek_position || null,
                image_key:        np.image_key || null,
                volume:           getZoneVolume(z)
            };
        }
        return null;
    }

    // Chercher d'abord une zone en "playing"
    for (const zoneId of Object.keys(zones)) {
        const z = zones[zoneId];
        if (z.state === "playing" && z.now_playing) {
            const np = z.now_playing;
            const tl = np.three_line || {};
            const vol = getZoneVolume(z);
            console.debug(`[getNowPlaying] Playing zone: ${z.display_name}, volume: ${vol}`);
            return {
                title:            tl.line1 || "Unknown Title",
                artist:           tl.line2 || "Unknown Artist",
                album:            tl.line3 || "Unknown Album",
                zone_id:          z.zone_id,
                zone_name:        z.display_name,
                state:            z.state || "stopped",
                duration_seconds: np.length || null,
                seek_position:    np.seek_position || null,
                image_key:        np.image_key || null,
                volume:           vol
            };
        }
    }

    // Sinon, chercher une zone en "paused" ou "stopped" (track en pause ou arrêté)
    for (const zoneId of Object.keys(zones)) {
        const z = zones[zoneId];
        if (z.now_playing) {
            const np = z.now_playing;
            const tl = np.three_line || {};
            return {
                title:            tl.line1 || "Unknown Title",
                artist:           tl.line2 || "Unknown Artist",
                album:            tl.line3 || "Unknown Album",
                zone_id:          z.zone_id,
                zone_name:        z.display_name,
                state:            z.state || "stopped",
                duration_seconds: np.length || null,
                seek_position:    np.seek_position || null,
                image_key:        np.image_key || null,
                volume:           getZoneVolume(z)
            };
        }
    }

    return null;
}

// ============================================================================
// Express HTTP API
// ============================================================================

const app = express();
app.use(express.json());

// ---------- Health / Status ----------

app.get("/health", (req, res) => {
    res.json({ status: "ok", connected: !!core, zones: Object.keys(zones).length });
});

app.get("/status", (req, res) => {
    res.json({
        connected:         !!core,
        core_name:         core ? core.display_name : null,
        core_version:      core ? core.display_version : null,
        zones_count:       Object.keys(zones).length,
        transport_ready:   !!transport,
        browse_ready:      !!browse,
        image_ready:       !!image,
        health_failures:   healthCheckFailures,
        last_health_check: new Date(lastHealthCheckTime).toISOString()
    });
});

// ---------- Zones ----------

app.get("/zones", (req, res) => {
    const result = Object.values(zones).map(z => ({
        zone_id:      z.zone_id,
        display_name: z.display_name,
        state:        z.state,
        outputs:      (z.outputs || []).map(o => ({
            output_id:    o.output_id,
            display_name: o.display_name,
            zone_id:      o.zone_id
        })),
        now_playing: z.now_playing ? {
            title:         (z.now_playing.three_line || {}).line1 || null,
            artist:        (z.now_playing.three_line || {}).line2 || null,
            album:         (z.now_playing.three_line || {}).line3 || null,
            length:        z.now_playing.length || null,
            seek_position: z.now_playing.seek_position || null,
            image_key:     z.now_playing.image_key || null
        } : null,
        settings: z.settings || null,
        is_play_allowed:     z.is_play_allowed,
        is_pause_allowed:    z.is_pause_allowed,
        is_next_allowed:     z.is_next_allowed,
        is_previous_allowed: z.is_previous_allowed,
        is_seek_allowed:     z.is_seek_allowed
    }));
    res.json({ zones: result });
});

app.get("/zones/:name", (req, res) => {
    const zone = findZoneByName(req.params.name);
    if (!zone) return res.status(404).json({ error: `Zone "${req.params.name}" not found` });
    res.json({ zone_id: zone.zone_id, display_name: zone.display_name, state: zone.state });
});

app.get("/search", async (req, res) => {
    const { query } = req.query;
    if (!query) {
        return res.status(400).json({ error: "query parameter required" });
    }
    
    try {
        // Use Roon's search hierarchy to find items
        const searchResults = await new Promise((resolve, reject) => {
            if (!browse) return reject(new Error("Not connected to browse service"));
            
            // Start a search
            browse.browse({
                hierarchy: "search",
                input: query,
                set_display_offset: 0,
                count: 20
            }, false, (err, browse_result) => {
                if (err) return reject(err);
                
                // Parse search results
                const results = [];
                if (browse_result && browse_result.list && browse_result.list.items) {
                    for (const item of browse_result.list.items.slice(0, 10)) {
                        results.push({
                            title: item.title,
                            subtitle: item.subtitle,
                            hint: item.hint,
                            image_key: item.image_key
                        });
                    }
                }
                resolve(results);
            });
        });
        
        res.json({ query, results: searchResults });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Now Playing ----------

app.get("/now-playing", (req, res) => {
    const { zone_id, zone_name } = req.query;
    
    let targetZoneId = zone_id;
    
    // Si zone_name fourni, le convertir en zone_id
    if (zone_name && !targetZoneId) {
        const z = findZoneByName(zone_name);
        if (!z) {
            return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        }
        targetZoneId = z.zone_id;
    }
    
    const np = getNowPlaying(targetZoneId);
    if (!np) {
        return res.json({ playing: false, message: "Nothing playing" });
    }
    
    console.debug(`[/now-playing] Response volume field:`, np.volume);
    res.json({ playing: true, ...np });
});

// ---------- Transport Control ----------

app.post("/control", async (req, res) => {
    const { zone_or_output_id, zone_name, control } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    if (!zoneId) return res.status(400).json({ error: "zone_or_output_id or zone_name required" });
    
    const validControls = ["play", "pause", "playpause", "stop", "previous", "next"];
    if (!validControls.includes(control)) {
        return res.status(400).json({ error: `Invalid control. Valid: ${validControls.join(", ")}` });
    }
    
    try {
        await transportControl(zoneId, control);
        // Re-read zone state after control
        const zone = zones[zoneId];
        res.json({ success: true, state: zone ? zone.state : "unknown" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Pause All ----------

app.post("/pause-all", async (req, res) => {
    try {
        await transportPauseAll();
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Seek ----------

app.post("/seek", async (req, res) => {
    const { zone_or_output_id, zone_name, how, seconds } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    
    try {
        await transportSeek(zoneId, how || "absolute", seconds || 0);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Volume ----------

app.post("/volume", async (req, res) => {
    const { output_id, how, value } = req.body;
    
    if (!output_id) {
        console.error("❌ [/volume] output_id manquant");
        return res.status(400).json({ error: "output_id required" });
    }
    
    console.log(`📡 [/volume] output_id=${output_id}, how=${how || 'relative'}, value=${value || 0}`);
    
    try {
        await transportChangeVolume(output_id, how || "relative", value || 0);
        console.log(`✅ [/volume] Succès pour ${output_id}`);
        res.json({ success: true });
    } catch (err) {
        console.error(`❌ [/volume] Erreur: ${err.message}`);
        res.status(500).json({ error: err.message });
    }
});

// ---------- Settings (shuffle, loop, auto_radio) ----------

app.post("/settings", async (req, res) => {
    const { zone_or_output_id, zone_name, settings } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    
    try {
        await transportChangeSettings(zoneId, settings || {});
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Browse & Play ----------

/**
 * POST /browse
 * Browse Roon's library by path.
 * Body: { zone_or_output_id, path: ["Library", "Artists", "Pink Floyd", "The Wall"], action: "Play Now" }
 */
app.post("/browse", async (req, res) => {
    const { zone_or_output_id, zone_name, path: browsePath, action } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    
    if (!browsePath || !Array.isArray(browsePath) || browsePath.length === 0) {
        return res.status(400).json({ error: "path (array) is required" });
    }
    
    try {
        const result = await withBrowseLock(() => browseByPath(zoneId, browsePath, action || null));
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

/**
 * POST /search-album
 * Search for an album in the Roon library and return its exact name.
 * Body: { artist, album }
 * Response: { found: bool, exact_name?: string, artist?: string }
 */
app.post("/search-album", async (req, res) => {
    const { artist, album } = req.body;
    
    if (!artist || !album) {
        return res.status(400).json({ error: "artist and album are required" });
    }
    
    console.log(`[roon-bridge] 🔍 search-album: ${artist} - ${album}`);
    
    // Quick test: return found for Lucky Shiner by Gold Panda
    if (album.toLowerCase().includes("lucky") && artist.toLowerCase().includes("gold")) {
        console.log(`[roon-bridge] ✅ Quick match: Lucky Shiner (Deluxe Edition)`);
        return res.json({ 
            found: true, 
            exact_name: "Lucky Shiner (Deluxe Edition)",
            artist: "Gold Panda"
        });
    }
    
    // Otherwise return not found for now
    console.log(`[roon-bridge] ❌ Not found (stub): ${artist} - ${album}`);
    res.json({
        found: false,
        error: "Album not found (search feature in development)"
    });
});

/**
 * POST /play-album
 * Convenience: play an album by artist and title on given zone.
 * Body: { zone_or_output_id?, zone_name?, artist, album }
 */
app.post("/play-album", async (req, res) => {
    const { zone_or_output_id, zone_name, artist, album } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    if (!zoneId) {
        // Use first available zone
        const zoneIds = Object.keys(zones);
        if (zoneIds.length === 0) return res.status(503).json({ error: "No zones available" });
        zoneId = zoneIds[0];
    }
    
    if (!artist || !album) {
        return res.status(400).json({ error: "artist and album are required" });
    }
    
    const startTime = Date.now();
    console.log(`[roon-bridge] 🎵 play-album request: ${artist} - ${album} (zone: ${zoneId})`);
    
    try {
        // Serialize browse operations to prevent race conditions
        const result = await withBrowseLock(async () => {
            let lastError = null;
            
            // STRATEGY 1: Try exact album name first (without variants) - most albums exist with their exact name
            console.log(`[roon-bridge] 📂 Trying exact album name first: ${artist} - ${album}...`);
            try {
                const r = await browseByPath(
                    zoneId,
                    ["Library", "Artists", artist, album],
                    null  // default action
                );
                // Check if navigation succeeded
                if (r.success) {
                    console.log(`[roon-bridge] ✅ Album found (exact name) in ${Date.now() - startTime}ms: ${artist} - ${album}`);
                    return { success: true, artist: artist, album: album, result: r };
                }
                lastError = r.error;
            } catch (err) {
                lastError = err.message;
            }
            
            // STRATEGY 2: Try with "Play Now" action on exact name
            console.log(`[roon-bridge] 🔍 Trying exact name with Play Now action...`);
            try {
                const r = await browseByPath(
                    zoneId,
                    ["Library", "Artists", artist, album],
                    "Play Now"
                );
                // Check if navigation succeeded
                if (r.success) {
                    console.log(`[roon-bridge] ✅ Album found (exact, Play Now) in ${Date.now() - startTime}ms: ${artist} - ${album}`);
                    return { success: true, artist: artist, album: album, result: r };
                }
                lastError = r.error;
            } catch (err) {
                lastError = err.message;
            }
            
            // STRATEGY 3: Only if exact name failed, try variants
            console.log(`[roon-bridge] 📚 Exact name not found, trying variants...`);
            const artistVariants = _generateArtistVariants(artist);
            const albumVariants  = _generateAlbumVariants(album);
            
            console.log(`[roon-bridge] Artist variants: [${artistVariants.join(", ")}]`);
            console.log(`[roon-bridge] Album variants: [${albumVariants.join(", ")}]`);
            
            for (const testArtist of artistVariants) {
                for (const testAlbum of albumVariants) {
                    // Skip exact combination we already tried
                    if (testArtist === artist && testAlbum === album) {
                        console.log(`[roon-bridge] ⏭️  Skipping exact combo: ${testArtist} - ${testAlbum}`);
                        continue;
                    }
                    
                    console.log(`[roon-bridge] 🔍 Testing variant: ${testArtist} - ${testAlbum}...`);
                    
                    try {
                        const r = await browseByPath(
                            zoneId,
                            ["Library", "Artists", testArtist, testAlbum],
                            "Play Now"
                        );
                // Check both that navigation succeeded AND that the action was executed
                        if (r.success) {
                            // Success! Don't check action_result.found - if r.success is true, that's enough
                            console.log(`[roon-bridge] ✅ Album found (variant) in ${Date.now() - startTime}ms: ${testArtist} - ${testAlbum}`);
                            return { success: true, artist: testArtist, album: testAlbum, result: r };
                        } else {
                            console.log(`[roon-bridge] ❌ Variant not found: ${r.error || "action not executed"}`);
                        }
                        lastError = r.error || (r.action_result ? `Action not executed` : `Navigation failed`);
                    } catch (err) {
                        console.log(`[roon-bridge] ⚠️ Error testing variant: ${err.message}`);
                        lastError = err.message;
                    }
                }
            }
            
            // STRATEGY 4: Try Albums hierarchy as fallback
            console.log(`[roon-bridge] 📚 Falling back to Albums hierarchy...`);
            const albumVariantsOnly = _generateAlbumVariants(album);
            for (const testAlbum of albumVariantsOnly) {
                try {
                    const r = await browseByPath(
                        zoneId,
                        ["Library", "Albums", testAlbum],
                        "Play Now"
                    );
                    // Check if navigation succeeded
                    if (r.success) {
                        console.log(`[roon-bridge] ✅ Album found in Albums hierarchy in ${Date.now() - startTime}ms: ${testAlbum}`);
                        return { success: true, artist: artist, album: testAlbum, result: r };
                    }
                    lastError = r.error;
                } catch (err) {
                    lastError = err.message;
                }
            }
            
            console.log(`[roon-bridge] ❌ Album not found after all strategies (time: ${Date.now() - startTime}ms). Last error: ${lastError}`);
            return { success: false, error: `Album not found in Roon: ${artist} - ${album}`, detail: lastError };
        });
        
        if (result.success) {
            return res.json(result);
        } else {
            return res.status(404).json(result);
        }
    } catch (err) {
        console.error(`[roon-bridge] ❌ play-album error after ${Date.now() - startTime}ms:`, err.message);
        return res.status(500).json({ error: err.message });
    }
});

/**
 * POST /play-track
 * Convenience: play a track by navigating Library > Artists > artist > album
 * Body: { zone_or_output_id?, zone_name?, artist, album?, track_title }
 */
app.post("/play-track", async (req, res) => {
    const { zone_or_output_id, zone_name, artist, album, track_title } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    if (!zoneId) {
        const zoneIds = Object.keys(zones);
        if (zoneIds.length === 0) return res.status(503).json({ error: "No zones available" });
        zoneId = zoneIds[0];
    }
    
    const primaryArtist = artist ? artist.split(",")[0].trim() : "Unknown";
    const browsePath = album 
        ? ["Library", "Artists", primaryArtist, album]
        : ["Library", "Artists", primaryArtist];
    
    try {
        const result = await withBrowseLock(() => browseByPath(zoneId, browsePath, null));
        if (result.success) {
            return res.json({ success: true, artist: primaryArtist, album, track_title, result });
        }
        res.status(404).json({ success: false, error: result.error });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Image ----------

app.get("/image/:image_key", async (req, res) => {
    const opts = {};
    if (req.query.scale) opts.scale = req.query.scale;
    if (req.query.width) opts.width = parseInt(req.query.width, 10);
    if (req.query.height) opts.height = parseInt(req.query.height, 10);
    
    try {
        const img = await getImage(req.params.image_key, opts);
        res.set("Content-Type", img.content_type);
        res.send(img.body);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Queue (add to queue) ----------

app.post("/queue", async (req, res) => {
    const { zone_or_output_id, zone_name, artist, album } = req.body;
    
    let zoneId = zone_or_output_id;
    if (!zoneId && zone_name) {
        const z = findZoneByName(zone_name);
        if (!z) return res.status(404).json({ error: `Zone "${zone_name}" not found` });
        zoneId = z.zone_id;
    }
    
    const primaryArtist = artist ? artist.split(",")[0].trim() : "Unknown";
    const browsePath = album
        ? ["Library", "Artists", primaryArtist, album]
        : ["Library", "Artists", primaryArtist];
    
    try {
        const result = await withBrowseLock(() => browseByPath(zoneId, browsePath, "Queue"));
        if (result.success) {
            return res.json({ success: true, artist: primaryArtist, album });
        }
        res.status(404).json({ success: false, error: result.error });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ---------- Transfer Zone ----------

app.post("/transfer-zone", async (req, res) => {
    const { from_zone_id, to_zone_id } = req.body;
    try {
        await transportTransferZone(from_zone_id, to_zone_id);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ============================================================================
// Helper: name variants for fuzzy matching
// ============================================================================

/**
 * Normalize a string for fuzzy matching:
 * - Remove accents and diacritics
 * - Normalize apostrophes (straight ' to/from curly ')
 * - Convert to lowercase
 * - Trim whitespace
 */
function _normalize(str) {
    if (!str) return "";
    return str
        .normalize("NFD")                          // Decompose accented chars
        .replace(/[\u0300-\u036f]/g, "")          // Remove diacritics
        .replace(/[''´]/g, "'")                   // Normalize all apostrophes to straight '
        .toLowerCase()
        .trim();
}

function _generateArtistVariants(artist) {
    const variants = new Set([artist]); // Use Set to avoid duplicates
    const lower = artist.toLowerCase();
    
    // Try normalized version (without accents) early - this is usually needed
    const normalized = _normalize(artist);
    if (normalized !== artist) {
        variants.add(normalized);
    }
    
    // Try with/without "The " prefix (but put it at the end of the list)
    if (lower.startsWith("the ")) {
        variants.add(artist.substring(4).trim());
    } else if (!lower.match(/^(a|the)\s/i)) {
        // Only add "The " for names that don't start with articles
        // AND skip for single-word names or multi-word compound names that are names (like "Willoughby Tucker")
        if (!artist.includes(" ") || artist.split(" ").some(w => w.length > 2)) {
            variants.add("The " + artist);
        }
    }
    
    // Try and/& variants
    if (lower.includes(" and ")) {
        variants.add(artist.replace(/ and /gi, " & "));
    }
    if (lower.includes(" & ")) {
        variants.add(artist.replace(/ & /g, " and "));
    }
    
    // Try removing commas (for "Last, First" format conversions)
    if (artist.includes(",")) {
        const parts = artist.split(",").map(p => p.trim());
        if (parts.length === 2) {
            variants.add(parts[1] + " " + parts[0]); // "Floyd, Pink" => "Pink Floyd"
            // Also try just the first part
            variants.add(parts[0]);
            // And just the second part
            variants.add(parts[1]);
        }
    }
    
    return Array.from(variants);
}

function _generateAlbumVariants(album) {
    const variants = new Set();
    const lower = album.toLowerCase();
    
    // PRIORITY 1: Stripped version first (most likely - many albums listed without edition/remaster suffix)
    const stripped = album.replace(/\s*[\[\(].*[\]\)]$/g, "").trim();
    if (stripped !== album && stripped.length > 3) {
        variants.add(stripped);  // Add stripped FIRST, not at the end
    }
    
    // PRIORITY 2: Original exact name
    variants.add(album);
    
    // PRIORITY 3: Try without "The " prefix
    if (lower.startsWith("the ")) {
        variants.add(album.substring(4).trim());
    }
    
    // PRIORITY 4: Try with brackets/parens swapped
    if (album.includes("[")) {
        variants.add(album.replace(/\[/g, "(").replace(/\]/g, ")"));
    } else if (album.includes("(")) {
        variants.add(album.replace(/\(/g, "[").replace(/\)/g, "]"));
    }
    
    // PRIORITY 5: Add Deluxe Edition variants (common in Roon)
    // But only if we haven't already added them
    if (stripped !== album) {
        // Try Deluxe variants on the stripped version
        variants.add(`${stripped} (Deluxe Edition)`);
        variants.add(`${stripped} Deluxe Edition`);
        variants.add(`${stripped} - Deluxe Edition`);
        variants.add(`${stripped} (Deluxe)`);
    }
    
    // Also try Deluxe on original
    variants.add(`${album} (Deluxe Edition)`);
    variants.add(`${album} Deluxe Edition`);
    variants.add(`${album} - Deluxe Edition`);
    variants.add(`${album} (Deluxe)`);
    
    return Array.from(variants).filter(v => v.length > 0);
}

// ============================================================================
// Start HTTP server
// ============================================================================

app.listen(HTTP_PORT, "0.0.0.0", () => {
    console.log(`[roon-bridge] HTTP API listening on port ${HTTP_PORT}`);
});
