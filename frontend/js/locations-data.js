// Bundled country -> city/town list used to populate location dropdowns.
// The United Kingdom is fully populated for the demo; other countries carry a
// handful of major cities each. The country <select> is built from the keys of
// this object, so adding a country here (with a city array) is all that is
// needed to extend both the Locations and Vendors forms.
// United Kingdom is kept first (it is the default); the rest are alphabetical.

const COUNTRY_CITIES = {
    "United Kingdom": [
        "London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool",
        "Bristol", "Sheffield", "Edinburgh", "Cardiff", "Leicester", "Nottingham",
        "Newcastle upon Tyne", "Southampton", "Portsmouth", "Reading",
        "Milton Keynes", "Coventry", "Brighton", "Kingston upon Hull", "Plymouth",
        "Derby", "Wolverhampton", "Stoke-on-Trent", "Norwich", "Swansea",
        "Aberdeen", "Dundee", "Belfast", "Bradford", "Luton", "Northampton",
        "Peterborough", "York", "Oxford", "Cambridge", "Exeter", "Bolton",
        "High Wycombe", "Hemel Hempstead", "Gatwick",
    ],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Gold Coast", "Hobart"],
    "Austria": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt"],
    "Belgium": ["Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges"],
    "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza", "Belo Horizonte", "Curitiba"],
    "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg", "Quebec City"],
    "China": ["Shanghai", "Beijing", "Shenzhen", "Guangzhou", "Chengdu", "Chongqing", "Tianjin", "Hangzhou"],
    "Denmark": ["Copenhagen", "Aarhus", "Odense", "Aalborg", "Esbjerg"],
    "Egypt": ["Cairo", "Alexandria", "Giza", "Shubra El Kheima", "Port Said", "Suez"],
    "Finland": ["Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu", "Turku"],
    "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Lille", "Bordeaux"],
    "Germany": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Düsseldorf", "Leipzig"],
    "Ghana": ["Accra", "Kumasi", "Tamale", "Sekondi-Takoradi", "Ashaiman", "Cape Coast"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad"],
    "Ireland": ["Dublin", "Cork", "Limerick", "Galway", "Waterford", "Drogheda"],
    "Italy": ["Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna", "Florence"],
    "Japan": ["Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo", "Fukuoka", "Kobe", "Kyoto"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "León", "Ciudad Juárez"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Groningen", "Tilburg"],
    "New Zealand": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga", "Dunedin"],
    "Nigeria": ["Lagos", "Kano", "Ibadan", "Abuja", "Port Harcourt", "Benin City", "Kaduna"],
    "Norway": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Drammen", "Kristiansand"],
    "Poland": ["Warsaw", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin"],
    "Portugal": ["Lisbon", "Porto", "Amadora", "Braga", "Coimbra", "Funchal"],
    "Saudi Arabia": ["Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Al Khobar", "Tabuk"],
    "Singapore": ["Singapore", "Jurong East", "Woodlands", "Tampines", "Bedok", "Changi"],
    "South Africa": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Gqeberha", "Bloemfontein", "East London"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Málaga", "Bilbao", "Palma"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping"],
    "Switzerland": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne", "Winterthur", "Lucerne"],
    "Turkey": ["Istanbul", "Ankara", "İzmir", "Bursa", "Adana", "Gaziantep", "Konya"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain", "Ajman", "Ras Al Khaimah", "Fujairah"],
    "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Atlanta"],
};

const DEFAULT_COUNTRY = "United Kingdom";

// Build <option> markup for the country <select>.
function countryOptionsHtml(selected) {
    return Object.keys(COUNTRY_CITIES)
        .map((c) => `<option value="${c}"${c === selected ? " selected" : ""}>${c}</option>`)
        .join("");
}

// Build <option> markup for the city <select>, scoped to the chosen country.
function cityOptionsHtml(country, selected) {
    const cities = COUNTRY_CITIES[country] || [];
    const opts = cities
        .map((city) => `<option value="${city}"${city === selected ? " selected" : ""}>${city}</option>`)
        .join("");
    // Allow the current value even if it is not in the list (legacy data).
    if (selected && !cities.includes(selected)) {
        return `<option value="${selected}" selected>${selected}</option>` + opts;
    }
    return `<option value="">Select city/town...</option>` + opts;
}
