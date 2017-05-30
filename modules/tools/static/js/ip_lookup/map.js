function initMap() {
  var uluru = {lat: parseInt(LAT), lng: parseInt(LONG)};
  var map = new google.maps.Map(document.getElementById('map1'), {
    zoom: 5,
    center: uluru
  });
  var marker = new google.maps.Marker({
    position: uluru,
    map: map
  });
}
