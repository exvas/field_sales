

// frappe.pages['location-sales'].on_page_load = async function(wrapper) {
//     let page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Employee Location Path',
//         single_column: true
//     });

//     // Container
//     let $wrapper = $(wrapper).find('.layout-main-section');
//     $wrapper.html(`
//         <div class="row">
//             <div class="col-md-4">
//                 <div class="form-group" id="employee_link"></div>
//                 <div class="form-group">
//                     <label for="log_date">Date</label>
//                     <input type="date" class="form-control" id="log_date">
//                 </div>
//                 <div class="form-group">
//                     <button class="btn btn-primary" id="show_path_btn">Show Path</button>
//                 </div>
//             </div>
//             <div class="col-md-8">
//                 <div id="map" style="height: 500px; border: 1px solid #ccc;"></div>
//             </div>
//         </div>
//     `);

//     // Create Employee Link field
//     let employee_control = frappe.ui.form.make_control({
//         parent: $('#employee_link'),
//         df: {
//             fieldtype: 'Link',
//             options: 'Employee',
//             label: 'Employee',
//             fieldname: 'employee_id',
//             placeholder: 'Select Employee'
//         },
//         render_input: true
//     });

//     await frappe.utils.sleep(100); // Ensure control is rendered

//     const date_input = $('#log_date');
//     const button = $('#show_path_btn');

//     // Initialize Leaflet map
//     window.map = L.map('map').setView([11.25, 75.80], 12);

//     // Add tiles
//     L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//         attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
//     }).addTo(map);

//     // Show path button click
//     button.on('click', function () {
//         let employee = employee_control.get_value();
//         let date = date_input.val();

//         if (!employee || !date) {
//             frappe.msgprint("Please select both Employee and Date.");
//             return;
//         }

//         fetch_and_render_map(employee, date);
//     });
// };

// function fetch_and_render_map(employee, date) {
//     frappe.call({
//         method: "field_sales.field_sales.page.location_sales.location_sales.get_location_data",
//         args: { employee, date },
//         callback: function(r) {
//             const data = r.message || [];

//             if (!data.length) {
//                 frappe.msgprint("No location data found.");
//                 return;
//             }

//             if (window.markersLayer) {
//                 window.markersLayer.clearLayers();
//             } else {
//                 window.markersLayer = L.layerGroup().addTo(map);
//             }

//             let latlngs = [];

//             data.forEach(point => {
//                 const lat = point.latitude;
//                 const lon = point.longitude;
//                 const time = point.time;

//                 const marker = L.marker([lat, lon]).bindPopup(`Time: ${time}`);
//                 window.markersLayer.addLayer(marker);
//                 latlngs.push([lat, lon]);
//             });

//             const bounds = L.latLngBounds(latlngs);
//             map.fitBounds(bounds);

//             if (window.pathLine) {
//                 map.removeLayer(window.pathLine);
//             }

//             window.pathLine = L.polyline(latlngs, { color: 'blue' }).addTo(map);
//         }
//     });
// }


frappe.pages['location-sales'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Location Sales',
        single_column: true
    });

    let map = null;

    // Load Leaflet Routing Machine JS and CSS
    frappe.require([
        "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.min.js",
        "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css"
    ], () => {
        render_ui();
    });

    function render_ui() {
        const html = `
            <div class="row">
                <div class="col-md-4">
                    <div class="form-group" id="employee_input_wrapper">
                        <label>Employee</label>
                    </div>
                    <div class="form-group">
                        <label>Date</label>
                        <input type="date" id="date_filter" class="form-control">
                    </div>
                    <button class="btn btn-primary" id="search_btn">Search</button>
                </div>
                <div class="col-md-8">
                    <div id="map" style="height: 500px; border: 1px solid #ccc; border-radius: 8px;"></div>
                </div>
            </div>
        `;

        $(page.body).html(html);

        // Setup Employee Link Field (only one)
        frappe.ui.form.make_control({
            df: {
                fieldtype: 'Link',
                options: 'Employee',
                reqd: 1,
                label: 'Employee',
                fieldname: 'employee_filter'
            },
            parent: $('#employee_input_wrapper'),
            render_input: true
        }).make_input(); // Important to call make_input

        // Initialize Leaflet map
        map = L.map('map').setView([20.5937, 78.9629], 5); // Default to India
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
        }).addTo(map);

        window.markersLayer = L.layerGroup().addTo(map);

        $('#search_btn').click(() => {
            const employee = $('[data-fieldname="employee_filter"] input').val();
            const date = $('#date_filter').val();

            if (!employee || !date) {
                frappe.msgprint('Please select both Employee and Date.');
                return;
            }

            fetch_and_render_map(employee, date);
        });
    }

    function fetch_and_render_map(employee, date) {
        frappe.call({
            method: "field_sales.field_sales.page.location_sales.location_sales.get_location_data",
            args: { employee, date },
            callback: function (r) {
                const data = r.message || [];

                if (!data.length) {
                    frappe.msgprint("No location data found.");
                    return;
                }

                // Clear old markers/routes
                if (window.markersLayer) window.markersLayer.clearLayers();
                if (window.routingControl) {
                    map.removeControl(window.routingControl);
                    window.routingControl = null;
                }

                let latlngs = [];

                data.forEach(point => {
                    const marker = L.marker([point.latitude, point.longitude])
                        .bindPopup(`Time: ${point.time}`);
                    window.markersLayer.addLayer(marker);
                    latlngs.push([point.latitude, point.longitude]);
                });

                map.fitBounds(L.latLngBounds(latlngs));

                if (latlngs.length >= 2) {
                    window.routingControl = L.Routing.control({
                        waypoints: latlngs.map(loc => L.latLng(loc[0], loc[1])),
                        routeWhileDragging: false,
                        show: false,
                        addWaypoints: false,
                        draggableWaypoints: false,
                        createMarker: () => null
                    }).addTo(map);
                }
            }
        });
    }
};
