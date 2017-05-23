google.maps.event.addDomListener(window, 'load', init);
function init() {
    var mapOptions1 = {
        zoom: 5
    };
    var mapElement1 = document.getElementById('map1');
    var map1 = new google.maps.Map(mapElement1, mapOptions1);
    var geocoder= new google.maps.Geocoder();
    geocoder.geocode( {'address' : COUNTRY_NAME}, function(results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
            map1.setCenter(results[0].geometry.location);
        }
    });
}