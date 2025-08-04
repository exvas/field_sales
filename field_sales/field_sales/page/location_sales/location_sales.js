


// // frappe.pages['location-sales'].on_page_load = async function(wrapper) {
// //     let page = frappe.ui.make_app_page({
// //         parent: wrapper,
// //         title: 'Employee Location Path',
// //         single_column: true
// //     });

// //     await new Promise((resolve) => {
// //         frappe.require([
// //             "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
// //             "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.min.js",
// //             "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
// //             "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css"
// //         ], resolve);
// //     });

// //     delete L.Icon.Default.prototype._getIconUrl;
// //     L.Icon.Default.mergeOptions({
// //         iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
// //         iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
// //         shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
// //     });

// //     let $wrapper = $(wrapper).find('.layout-main-section');
// //     $wrapper.html(`
// //         <div class="row">
// //             <div class="col-md-4">
// //                 <div class="form-group" id="employee_link"></div>
// //                 <div class="form-group">
// //                     <div id="employee_name_display" style="font-weight: 600; color: #555; margin-top: -10px; margin-bottom: 10px;"></div>
// //                 </div>
// //                 <div class="form-group">
// //                     <label for="log_date">Date</label>
// //                     <input type="date" class="form-control" id="log_date">
// //                 </div>
// //                 <div class="form-group">
// //                     <button class="btn btn-primary" id="show_path_btn">Show Path</button>
// //                 </div>
// //                 <div class="form-group">
// //                     <label>Location Names</label>
// //                     <div id="location_names_list" style="
// //                         max-height: 400px;
// //                         overflow-y: auto;
// //                         border-left: 3px solid #007bff;
// //                         padding-left: 15px;
// //                         margin-top: 10px;
// //                         position: relative;
// //                     "></div>
// //                 </div>
// //             </div>
// //             <div class="col-md-8">
// //                 <div id="map" style="height: 500px; border: 1px solid #ccc; border-radius: 8px;"></div>
// //             </div>
// //         </div>
// //     `);

// //     let employee_control = frappe.ui.form.make_control({
// //         parent: $('#employee_link'),
// //         df: {
// //             fieldtype: 'Link',
// //             options: 'Employee',
// //             label: 'Employee',
// //             fieldname: 'employee_id',
// //             placeholder: 'Select Employee',
// //             change: function () {
// //                 const employee_id = employee_control.get_value();
// //                 if (employee_id) {
// //                     frappe.db.get_value("Employee", employee_id, "employee_name").then(r => {
// //                         const name = r.message.employee_name || "";
// //                         $('#employee_name_display').html(`Name: ${name}`);
// //                     });
// //                 } else {
// //                     $('#employee_name_display').html('');
// //                 }
// //             }
// //         },
// //         render_input: true
// //     });

// //     await frappe.utils.sleep(100);

// //     const date_input = $('#log_date');
// //     const button = $('#show_path_btn');

// //     window.map = L.map('map').setView([20.5937, 78.9629], 6);

// //     L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
// //         attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
// //         maxZoom: 18
// //     }).addTo(map);

// //     window.markersLayer = L.layerGroup().addTo(map);

// //     button.on('click', function () {
// //         let employee = employee_control.get_value();
// //         let date = date_input.val();

// //         if (!employee || !date) {
// //             frappe.msgprint("Please select both Employee and Date.");
// //             return;
// //         }

// //         $('#location_names_list').html("Fetching location names...");
// //         fetch_and_render_map(employee, date);
// //     });
// // };

// // async function fetch_and_render_map(employee, date) {
// //     frappe.call({
// //         method: "field_sales.field_sales.page.location_sales.location_sales.get_location_data",
// //         args: { employee, date },
// //         callback: async function (r) {
// //             const res = r.message;

// //             if (!res || (!res.location_entries?.length && !res.customer_visits?.length)) {
// //                 frappe.msgprint("No location data found.");
// //                 $('#location_names_list').html('');
// //                 return;
// //             }

// //             const combined = [];

// //             // Add customer visits first
// //             if (res.customer_visits?.length) {
// //                 for (const visit of res.customer_visits) {
// //                     combined.push({
// //                         latitude: visit.latitude,
// //                         longitude: visit.longitude,
// //                         time: visit.time || "N/A",
// //                         label: `Customer Visit: ${visit.customer_name}`,
// //                         type: 'customer'
// //                     });
// //                 }
// //             }

// //             // Add employee logs next
// //             if (res.location_entries?.length) {
// //                 for (const entry of res.location_entries) {
// //                     combined.push({
// //                         latitude: entry.latitude,
// //                         longitude: entry.longitude,
// //                         time: entry.time || "N/A",
// //                         label: `Employee Log`,
// //                         type: 'employee'
// //                     });
// //                 }
// //             }

// //             // Sort by time
// //             combined.sort((a, b) => {
// //                 const t1 = new Date(`1970-01-01T${a.time}`);
// //                 const t2 = new Date(`1970-01-01T${b.time}`);
// //                 return t1 - t2;
// //             });

// //             if (window.markersLayer) window.markersLayer.clearLayers();
// //             if (window.routingControl) {
// //                 window.map.removeControl(window.routingControl);
// //                 window.routingControl = null;
// //             }

// //             const locationList = document.getElementById("location_names_list");
// //             locationList.innerHTML = '';
// //             let latlngs = [];

// //             for (const point of combined) {
// //                 const { latitude: lat, longitude: lon, time, label, type } = point;

// //                 // Reverse geocode
// //                 const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`);
// //                 const json = await res.json();
// //                 const display_name = json.display_name || `Lat: ${lat}, Lon: ${lon}`;

// //                 const location_item = document.createElement("div");
// //                 location_item.style.position = 'relative';
// //                 location_item.style.marginBottom = '20px';
// //                 location_item.style.opacity = 0.4;

// //                 location_item.innerHTML = `
// //                     <div style="position: absolute; left: -15px; top: 2px; width: 10px; height: 10px; background-color: ${type === 'customer' ? 'green' : '#007bff'}; border-radius: 50%;"></div>
// //                     <div style="font-size: 13px;">
// //                         <div><b>${label}</b></div>
// //                         <div><b>Time:</b> ${time}</div>
// //                         <div><b>Location:</b> ${display_name}</div>
// //                     </div>
// //                 `;

// //                 locationList.appendChild(location_item);

// //                 // const marker = L.marker([lat, lon]).bindPopup(`${label}<br>Time: ${time}`);
// //                 // window.markersLayer.addLayer(marker);
// //                 const color = type === 'customer' ? 'green' : 'blue';

// //                 const marker = L.circleMarker([lat, lon], {
// //                     radius: 8,
// //                     fillColor: color,
// //                     color: color,
// //                     weight: 1,
// //                     opacity: 1,
// //                     fillOpacity: 0.8
// //                 }).bindPopup(`${label}<br>Time: ${time}`);

// //                 window.markersLayer.addLayer(marker);

// //                 latlngs.push([lat, lon]);

// //                 await new Promise(res => setTimeout(res, 600));
// //                 location_item.style.opacity = 1;
// //                 location_item.scrollIntoView({ behavior: "smooth", block: "start" });
// //             }

// //             window.map.fitBounds(L.latLngBounds(latlngs));

// //             if (latlngs.length >= 2) {
// //                 window.routingControl = L.Routing.control({
// //                     waypoints: latlngs.map(loc => L.latLng(loc[0], loc[1])),
// //                     routeWhileDragging: false,
// //                     show: false,
// //                     addWaypoints: false,
// //                     draggableWaypoints: false,
// //                     createMarker: () => null
// //                 }).addTo(window.map);
// //             }
// //         }
// //     });
// // }


frappe.pages['location-sales'].on_page_load = async function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Location Path',
        single_column: true
    });

    await new Promise((resolve) => {
        frappe.require([
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.min.js",
            "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js",
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
            "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css",
            "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css",
            "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"
        ], resolve);
    });

    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });

    let $wrapper = $(wrapper).find('.layout-main-section');
    $wrapper.html(`
        <div class="row">
            <div class="col-md-4">
                <div class="form-group" id="employee_link"></div>
                <div class="form-group">
                    <div id="employee_name_display" style="font-weight: 600; color: #555; margin-top: -10px; margin-bottom: 10px;"></div>
                </div>
                <div class="form-group">
                    <label for="log_date">Date</label>
                    <input type="date" class="form-control" id="log_date">
                </div>
                <div class="form-group">
                    <button class="btn btn-primary" id="show_path_btn">Show Path</button>
                </div>
                <div class="form-group">
                    <label>Location Names</label>
                    <div id="location_names_list" style="
                        max-height: 400px;
                        overflow-y: auto;
                        border-left: 3px solid #007bff;
                        padding-left: 15px;
                        margin-top: 10px;
                        position: relative;
                    "></div>
                </div>
            </div>
            <div class="col-md-8">
                <div id="map" style="height: 500px; border: 1px solid #ccc; border-radius: 8px;"></div>
            </div>
        </div>
    `);

    let employee_control = frappe.ui.form.make_control({
        parent: $('#employee_link'),
        df: {
            fieldtype: 'Link',
            options: 'Employee',
            label: 'Employee',
            fieldname: 'employee_id',
            placeholder: 'Select Employee',
            change: function () {
                const employee_id = employee_control.get_value();
                if (employee_id) {
                    frappe.db.get_value("Employee", employee_id, "employee_name").then(r => {
                        const name = r.message.employee_name || "";
                        $('#employee_name_display').html(`Name: ${name}`);
                    });
                } else {
                    $('#employee_name_display').html('');
                }
            }
        },
        render_input: true
    });

    await frappe.utils.sleep(100);

    const date_input = $('#log_date');
    const button = $('#show_path_btn');

    window.map = L.map('map').setView([20.5937, 78.9629], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);

    window.markersLayer = L.markerClusterGroup();
    window.map.addLayer(window.markersLayer);

    button.on('click', function () {
        let employee = employee_control.get_value();
        let date = date_input.val();

        if (!employee || !date) {
            frappe.msgprint("Please select both Employee and Date.");
            return;
        }

        $('#location_names_list').html("Fetching location names...");
        fetch_and_render_map(employee, date);
    });
};

async function fetch_and_render_map(employee, date) {
    frappe.call({
        method: "field_sales.field_sales.page.location_sales.location_sales.get_location_data",
        args: { employee, date },
        callback: async function (r) {
            const res = r.message;

            if (!res || (!res.location_entries?.length && !res.customer_visits?.length)) {
                frappe.msgprint("No location data found.");
                $('#location_names_list').html('');
                return;
            }

            const combined = [];

            if (res.customer_visits?.length) {
                for (const visit of res.customer_visits) {
                    combined.push({
                        latitude: visit.latitude,
                        longitude: visit.longitude,
                        time: visit.time || "N/A",
                        label: `Customer Visit: ${visit.customer_name}`,
                        type: 'customer'
                    });
                }
            }

            if (res.location_entries?.length) {
                for (const entry of res.location_entries) {
                    combined.push({
                        latitude: entry.latitude,
                        longitude: entry.longitude,
                        time: entry.time || "N/A",
                        label: `Employee Log`,
                        type: 'employee'
                    });
                }
            }

            combined.sort((a, b) => new Date(`1970-01-01T${a.time}`) - new Date(`1970-01-01T${b.time}`));

            if (window.markersLayer) window.markersLayer.clearLayers();
            if (window.routingControl) {
                window.map.removeControl(window.routingControl);
                window.routingControl = null;
            }

            const locationList = document.getElementById("location_names_list");
            locationList.innerHTML = '';
            let latlngs = [];

            for (const point of combined) {
                const { latitude: lat, longitude: lon, time, label, type } = point;

                let display_name = `Lat: ${lat}, Lon: ${lon}`;
                try {
                    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`);
                    const json = await res.json();
                    display_name = json.display_name || display_name;
                } catch {}

                const location_item = document.createElement("div");
                location_item.style.marginBottom = '20px';
                location_item.innerHTML = `
                    <div style="position: relative">
                        <div style="position: absolute; left: -15px; top: 2px; width: 10px; height: 10px; background-color: ${type === 'customer' ? 'green' : '#007bff'}; border-radius: 50%;"></div>
                        <div style="font-size: 13px;">
                            <div><b>${label}</b></div>
                            <div><b>Time:</b> ${time}</div>
                            <div><b>Location:</b> ${display_name}</div>
                        </div>
                    </div>
                `;

                locationList.appendChild(location_item);

                const marker = L.circleMarker([lat, lon], {
                    radius: 6,
                    fillColor: type === 'customer' ? 'green' : 'blue',
                    color: '#000',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                }).bindPopup(`${label}<br>Time: ${time}`);

                window.markersLayer.addLayer(marker);
                latlngs.push([lat, lon]);
            }

            window.map.fitBounds(L.latLngBounds(latlngs));

            if (latlngs.length >= 2) {
                window.routingControl = L.Routing.control({
                    waypoints: latlngs.map(p => L.latLng(p[0], p[1])),
                    routeWhileDragging: false,
                    addWaypoints: false,
                    draggableWaypoints: false,
                    createMarker: () => null
                }).addTo(window.map);
            }
        }
    });
}

