
frappe.pages['location-sales'].on_page_load = async function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Sales Person Location Path',
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
                <div class="form-group" id="sales_person_link"></div>
                
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

    document.getElementById("log_date").valueAsDate = new Date();

    let sales_person_control = frappe.ui.form.make_control({
        parent: $('#sales_person_link'),
        df: {
            fieldtype: 'Link',
            options: 'Sales Person',
            label: 'Sales Person',
            fieldname: 'sales_person_id',
            placeholder: 'Select Sales Person',
            change: function () {
                const sales_person = sales_person_control.get_value();
                if (sales_person) {
                    frappe.db.get_value("Sales Person", sales_person, "sales_person_name").then(r => {
                        const name = r.message.sales_person_name || "";
                        $('#sales_person_name_display').html(`Name: ${name}`);
                    });
                } else {
                    $('#sales_person_name_display').html('');
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
        let sales_person = sales_person_control.get_value();
        let date = date_input.val();

        if (!sales_person || !date) {
            frappe.msgprint("Please select both Sales Person and Date.");
            return;
        }

        $('#location_names_list').html("Fetching location names...");
        fetch_and_render_map(sales_person, date);
    });
};

async function fetch_and_render_map(sales_person, date) {
    frappe.call({
        method: "field_sales.field_sales.page.location_sales.location_sales.get_location_data",
        args: { sales_person, date },
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

            // if (res.location_entries?.length) {
            //     for (const entry of res.location_entries) {
            //         combined.push({
            //             latitude: entry.latitude,
            //             longitude: entry.longitude,
            //             time: entry.time || "N/A",
            //             label: `Sales Person Log`,
            //             type: 'sales_person',
            //             type: entry.entry_type ? entry.entry_type.toLowerCase() : ''

            //         });
            //     }
            // }
            if (res.location_entries?.length) {
    for (const entry of res.location_entries) {
        combined.push({
            latitude: entry.latitude,
            longitude: entry.longitude,
            time: entry.time || "N/A",
            label: `Sales Person Location (${entry.entry_type || ''})`,
            type: entry.entry_type ? entry.entry_type.toLowerCase() : 'sales_person'
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
