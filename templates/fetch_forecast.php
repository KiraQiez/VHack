<?php

header("Content-Type: application/json");

if (!isset($_GET['locationId'])) {
    echo json_encode(["error" => "No town selected"]);
    exit;
}

$locationId = $_GET['locationId'];
$start_date = date("Y-m-d"); // Use today's date
$end_date = date("Y-m-d");

$api_url = "https://api.met.gov.my/v2.1/data?datasetid=FORECAST&datacategoryid=GENERAL&locationid=$locationId&start_date=$start_date&end_date=$end_date";

$headers = [
    "Authorization: METToken 31baf53255cd39bbe37efa2463824e9b60273431"
];

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// Log API response for debugging
file_put_contents("forecast_log.txt", $response);

if ($http_code == 200) {
    $data = json_decode($response, true);

    if (!isset($data['results']) || empty($data['results'])) {
        echo json_encode(["error" => "No forecast data found"]);
        exit;
    }

    // Filter results to only include FSIGW
    $filteredResults = array_filter($data['results'], function ($entry) {
        return $entry['datatype'] === "FSIGW";
    });

    if (empty($filteredResults)) {
        echo json_encode(["error" => "No significant weather data (FSIGW) found"]);
        exit;
    }

    $forecastData = [];
    foreach ($filteredResults as $entry) {
        $forecastData[] = [
            "date" => $entry['date'],
            "weather" => $entry['value'], // Forecast description
        ];
    }

    echo json_encode($forecastData);
} else {
    echo json_encode(["error" => "Failed to fetch forecast (HTTP Code: $http_code)"]);
}
