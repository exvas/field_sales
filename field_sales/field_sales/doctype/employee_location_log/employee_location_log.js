// Copyright (c) 2025, vijila@teambackoffice.com and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee Location Log", {
// 	refresh(frm) {

// 	},
// });


// frappe.ui.form.on('Employee Location Log', {
//     refresh: function(frm) {
//         if (frm.doc.__islocal) return;
//         console.log("SCRIPT LOADED");

//         // Destroy old map if already initialized
//         if (frm.mapInstance && frm.mapInstance.remove) {
//             frm.mapInstance.remove();
//         }

//         const map_container = frm.fields_dict.map_html.$wrapper;
//         map_container.html(`<div id="leaflet_map" style="height: 400px;"></div>`);

//         // Load Leaflet CSS
//         if (!document.getElementById("leaflet_css")) {
//             const link = document.createElement("link");
//             link.rel = "stylesheet";
//             link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
//             link.id = "leaflet_css";
//             document.head.appendChild(link);
//         }

//         // Load Leaflet JS
//         frappe.require("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", () => {
//             // Use setTimeout to wait for form to finish loading child table properly
//             setTimeout(() => {
//                 const locations = frm.doc.locations || [];

//                 console.log("Employee Location Entries:", locations);

//                 const map = L.map("leaflet_map").setView([11.5, 75.7], 10);
//                 frm.mapInstance = map; // save reference to destroy later

//                 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//                     maxZoom: 18
//                 }).addTo(map);

//                 const latlngs = [];

//                 locations.forEach(entry => {
//                     if (entry.latitude && entry.longitude) {
//                         const lat = parseFloat(entry.latitude);
//                         const lng = parseFloat(entry.longitude);
//                         console.log(`Lat: ${lat}, Lng: ${lng}`);

//                         if (!isNaN(lat) && !isNaN(lng)) {
//                             latlngs.push([lat, lng]);
//                             L.marker([lat, lng]).addTo(map)
//                                 .bindPopup(`Lat: ${lat}, Lng: ${lng}`);
//                         }
//                     }
//                 });

//                 if (latlngs.length) {
//                     L.polyline(latlngs, { color: 'blue' }).addTo(map);
//                     map.fitBounds(latlngs);
//                 }
//             }, 300); // 300ms delay helps ensure child table is ready
//         });
//     }
// });


frappe.ui.form.on('Employee Location Log', {
    refresh: function (frm) {
        if (frm.doc.__islocal) return;
        console.log("SCRIPT LOADED");

        // Destroy old map if already initialized
        if (frm.mapInstance && frm.mapInstance.remove) {
            frm.mapInstance.remove();
        }

        const map_container = frm.fields_dict.map_html.$wrapper;
        map_container.html(`<div id="leaflet_map" style="height: 400px;"></div>`);

        // Load Leaflet CSS
        if (!document.getElementById("leaflet_css")) {
            const leaflet_css = document.createElement("link");
            leaflet_css.rel = "stylesheet";
            leaflet_css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
            leaflet_css.id = "leaflet_css";
            document.head.appendChild(leaflet_css);
        }

        // Load Routing Machine CSS
        if (!document.getElementById("leaflet_routing_css")) {
            const routing_css = document.createElement("link");
            routing_css.rel = "stylesheet";
            routing_css.href = "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css";
            routing_css.id = "leaflet_routing_css";
            document.head.appendChild(routing_css);
        }

        // Load Leaflet and Routing Machine JS
        frappe.require([
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.min.js"
        ], () => {
            setTimeout(() => {
                const locations = frm.doc.locations || [];
                console.log("Employee Location Entries:", locations);

                const map = L.map("leaflet_map").setView([11.5, 75.7], 10);
                frm.mapInstance = map;

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 18
                }).addTo(map);

                // Custom icons based on entry_type
                const greenIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
                    shadowSize: [41, 41]
                });

                const redIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
                    shadowSize: [41, 41]
                });

                const blueIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
                    shadowSize: [41, 41]
                });

                const latlngs = [];

                locations.forEach(entry => {
                    if (entry.latitude && entry.longitude) {
                        const lat = parseFloat(entry.latitude);
                        const lng = parseFloat(entry.longitude);
                        const date = entry.date || entry.timestamp || "";
                        const location_name = entry.location_name || entry.address || "Unknown";
                        const entry_type = entry.entry_type || "Track";

                        if (!isNaN(lat) && !isNaN(lng)) {
                            latlngs.push([lat, lng]);

                            // Choose icon color based on entry_type
                            let markerIcon = blueIcon;
                            if (entry_type.toLowerCase() === 'check-in') {
                                markerIcon = greenIcon;
                            } else if (entry_type.toLowerCase() === 'check-out') {
                                markerIcon = redIcon;
                            }

                            const popupText = `
                                <b>Type:</b> ${entry_type}<br>
                                <b>Location:</b> ${location_name}<br>
                                <b>Date/Time:</b> ${date}<br>
                                <b>Lat:</b> ${lat}<br>
                                <b>Lng:</b> ${lng}
                            `;

                            L.marker([lat, lng], { icon: markerIcon }).addTo(map).bindPopup(popupText);
                        }
                    }
                });

                if (latlngs.length >= 2) {
                    L.Routing.control({
                        waypoints: latlngs.map(coords => L.latLng(coords[0], coords[1])),
                        routeWhileDragging: false,
                        show: false,
                        addWaypoints: false,
                        draggableWaypoints: false,
                        createMarker: function () { return null; } // Prevent Routing Machine from adding its own markers
                    }).addTo(map);

                    map.fitBounds(latlngs);
                }
            }, 300);
        });
    }
});
