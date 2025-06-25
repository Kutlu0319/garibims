<?php

function getPageContent($url) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
    $html = curl_exec($ch);
    curl_close($ch);
    return $html;
}

function getM3U8Links($html, $quality = "1080p") {
    preg_match_all('/https?:\/\/.*?\.m3u8/', $html, $matches);
    $filteredLinks = [];

    foreach ($matches[0] as $link) {
        if (strpos($link, $quality) !== false) {
            $filteredLinks[] = $link;
        }
    }

    return $filteredLinks;
}

function getSubtitles($html) {
    preg_match_all('/"file":"(.*?)","kind":"captions","label":"(.*?)"/', $html, $matches);
    $subtitles = [];

    foreach ($matches[1] as $key => $link) {
        $subtitles[] = [
            'lang' => $matches[2][$key],
            'url' => "https://www.hdfilmcehennemi.nl" . $link
        ];
    }

    return $subtitles;
}

function getMovieDetails($html) {
    $doc = new DOMDocument();
    @$doc->loadHTML($html);
    
    $title = "";
    $rating = "";
    foreach ($doc->getElementsByTagName('h1') as $h1) {
        if (strpos($h1->textContent, "izle") !== false) {
            $title = trim(str_replace(" izle", "", $h1->textContent));
            break;
        }
    }
    foreach ($doc->getElementsByTagName('span') as $span) {
        if (strpos($span->textContent, "IMDB") !== false) {
            $rating = trim(str_replace("IMDB: ", "", $span->textContent));
            break;
        }
    }
    
    return ["title" => $title, "rating" => $rating];
}

// HDFilmCehennemi sayfasının URL'si
$url = "https://www.hdfilmcehennemi.nl";
$html = getPageContent($url);

$m3u8_links = getM3U8Links($html, "1080p");  // Kaliteyi 1080p olarak filtreliyor
$subtitles = getSubtitles($html);
$movieDetails = getMovieDetails($html);

if (!empty($m3u8_links)) {
    $playlist = "#EXTM3U\n";
    $playlist .= "#EXTINF:-1, {$movieDetails['title']} (IMDB: {$movieDetails['rating']})\n";

    foreach ($m3u8_links as $link) {
        $playlist .= "$link\n";
    }

    foreach ($subtitles as $sub) {
        $playlist .= "#EXTVLCOPT:sub-file={$sub['url']}\n";
    }

    file_put_contents("hdfilm_playlist.m3u", $playlist);
    echo "M3U playlist oluşturuldu: hdfilm_playlist.m3u";
} else {
    echo "M3U8 bağlantıları bulunamadı.";
}

?>