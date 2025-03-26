<?php

header("Content-Type: application/json");

if (!isset($_GET['stateId'])) {
    echo json_encode(["error" => "No state selected"]);
    exit;
}

$stateId = $_GET['stateId'];
$api_url = "https://api.met.gov.my/v2.1/locations?locationcategoryid=TOWN";

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
file_put_contents("towns_log.txt", $response);

if ($http_code == 200) {
    $data = json_decode($response, true);

    if (!isset($data['results']) || empty($data['results'])) {
        echo json_encode(["error" => "No towns found"]);
        exit;
    }

    $towns = [];
    foreach ($data['results'] as $entry) {
        if ($entry['locationrootid'] === $stateId) { // Filter towns by selected state
            $towns[] = [
                "id" => $entry['id'],
                "name" => $entry['name']
            ];
        }
    }

    echo json_encode($towns);
} else {
    echo json_encode(["error" => "Failed to fetch towns (HTTP Code: $http_code)"]);
}
