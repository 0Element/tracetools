google.maps.event.addDomListener(window, 'load', init);
function init() {
    var mapOptions1 = {
        zoom: 5
    };
    var mapElement1 = document.getElementById('map1');
    var map1 = new google.maps.Map(mapElement1, mapOptions1);
    var objectPosition = {lat: parseInt(LAT), lng: parseInt(LONG)};
    map1.setCenter(objectPosition);
    var marker = new google.maps.Marker({
        position: objectPosition,
        map: map1
    });
}