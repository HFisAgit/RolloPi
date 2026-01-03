#https://github.com/JunusErgin/php-kontaktbuch/tree/6bfee1b36af1daf4229a1a10dc73f2c93d33a45b
<?php
# === Monolog Logging Setup ===
# Autoloader einbinden (nach Composer-Installation vorhanden)
# Try common vendor locations and provide a lightweight fallback logger if Monolog is not available.
$autoload_found = false;
if (file_exists(__DIR__ . '/vendor/autoload.php')) {
    require_once __DIR__ . '/vendor/autoload.php';
    $autoload_found = true;
} elseif (file_exists(__DIR__ . '/../vendor/autoload.php')) {
    require_once __DIR__ . '/../vendor/autoload.php';
    $autoload_found = true;
}

if ($autoload_found && class_exists('Monolog\\Logger')) {
    # Logger initialisieren (Syslog-Handler) using fully-qualified class names
    $log = new \Monolog\Logger('webseite');
    $log->pushHandler(new \Monolog\Handler\SyslogHandler('webseite', LOG_USER, \Monolog\Logger::INFO));
} else {
    # Fallback logger: einfache wrapper-Objekt mit info/error Methoden
    $log = new class {
        public function info($msg, $context = []) {
            error_log("INFO: $msg " . json_encode($context));
        }
        public function error($msg, $context = []) {
            error_log("ERROR: $msg " . json_encode($context));
        }
    };
    $log->info('Monolog nicht gefunden, verwende Fallback-Logger');
}

# Beispiel-Logeintrag (wird bei jedem Seitenaufruf geschrieben)
$log->info('index.php aufgerufen', [
    'remote_addr' => $_SERVER['REMOTE_ADDR'] ?? null,
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? null
]);

# Lade Hardware-Konfiguration zu Beginn
$path_to_hardware_config = "/var/www/html/hardware_config_Brentanoweg.json";
# $path_to_hardware_config = "/var/www/html/hardware_config_AmLohrein.json";
$house_name = 'Brentanoweg';
$house_number = '8';
if (file_exists($path_to_hardware_config)) {
    $hardware_text = file_get_contents($path_to_hardware_config, true);
    $hardware_config = json_decode($hardware_text, true);
    if ($hardware_config) {
        $house_name = $hardware_config['house_name'] ?? 'Brentanoweg';
        $house_number = $hardware_config['house_number'] ?? '8';
    }
}
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">

</head>

<body>
    # Kopfzeile
    <div class="menubar">
        <h1>Haussteuerung</h1>

        <div class="myname">
            <div class="avatar"><?php echo htmlspecialchars($house_number); ?></div><?php echo htmlspecialchars($house_name); ?>
        </div>
    </div>


    <div class="main">
        # Hauptmenue
        <div class="menu">
            <a href="index.php?page=start"><img src="img/home.svg"> Start</a>
            <a href="index.php?page=rollaeden"><img src="img/book.svg"> Rolläden</a>
            <a href="index.php?page=luefter"><img src="img/add.svg"> Lüfter</a>
            <a href="index.php?page=editRules"><img src="img/book.svg"> Regeln</a>
            <a href="index.php?page=legal"><img src="img/legal.svg"> Impressum</a>
        </div>

        # Hauptbereich
        <div class="content">

            <?php
            $headline = 'Herzlich willkommen';
            $rules = [];
            $luefter = [];
            $rollaeden = [];
            $path_to_regeln = "/home/pi/RolloPi/ramdisk/regeln.json";
            $path_to_reloadRegeln = '/home/pi/RolloPi/ramdisk/reloadRegeln.txt';
            $path_to_rolladiono = "cd /home/pi/RolloPi && python3 -m drivers.Rolladoino";
            $path_to_suntimes = "/home/pi/RolloPi/ramdisk/suntimes.json";
            $path_to_temperaturVals = "/home/pi/RolloPi/ramdisk/temperatures.json";

            # lade Rolladen-Konfiguration aus der bereits geladenen Hardware-Config
            if (isset($hardware_config) && isset($hardware_config['rollaeden'])) {
                $rollaeden = $hardware_config['rollaeden'];
            }

            ########################################################################

            # lade suntimes aus Datei
            if (file_exists($path_to_suntimes)) {
                $textsun = file_get_contents($path_to_suntimes, true);
                $suntimes = json_decode($textsun, true);
            }
            else {
                $log->error('Suntimes Datei nicht gefunden: ' . $path_to_suntimes);
            }
            
            # lade Temperaturwerte aus Datei
            if (file_exists($path_to_temperaturVals)) {
                $texttemp = file_get_contents($path_to_temperaturVals, true);
                $tempvals = json_decode($texttemp, true);
            }
            else {
                $log->error('Temperaturwerte Datei nicht gefunden: ' . $path_to_temperaturVals);
            }

            # lade Regeln aus Datei
            if (file_exists($path_to_regeln)) {
                $text = file_get_contents($path_to_regeln, true);
                $rules = json_decode($text, true);
            }
            else {
                $log->error('Regeln Datei nicht gefunden: ' . $path_to_regeln);
            }

            # Speichere neue Regeln falls nötig
            if (isset($_POST['morningearly'])) {
                if (($timestamp = strtotime($_POST['morningearly'])) === false) {
                    echo "ERROR die Zeit hat das falsche Format.";
                } else {
                    echo "Jetzt speichern!";
                    $rules['morgens']['early'] = date('G:i:s', $timestamp);
                    print_r($rules);
                    # ich habe keine schreibrechte... glaube ich
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                }
            }
            if (isset($_POST['morninglate'])) {
                if (($timestamp = strtotime($_POST['morninglate'])) === false) {
                    echo "ERROR die Zeit hat das falsche Format.";
                } else {
                    echo "Jetzt speichern!";
                    $rules['morgens']['late'] = date('G:i:s', $timestamp);
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                }
            }
            if (isset($_POST['eveningearly'])) {
                if (($timestamp = strtotime($_POST['eveningearly'])) === false) {
                    echo "ERROR die Zeit hat das falsche Format.";
                } else {
                    echo "Jetzt speichern!";
                    $rules['abends']['early'] = date('G:i:s', $timestamp);
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                }
            }
            if (isset($_POST['eveninglate'])) {
                if (($timestamp = strtotime($_POST['eveninglate'])) === false) {
                    echo "ERROR die Zeit hat das falsche Format.";
                } else {
                    echo "Jetzt speichern!";
                    $rules['abends']['late'] = date('G:i:s', $timestamp);
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                }
            }
            if (isset($_POST['Sonne'])) {
                if ($_POST['Sonne'] == "True" || $_POST['Sonne'] == "true") {
                    echo "Jetzt speichern!";
                    $rules['sonne']['ein'] = "true";
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                } else if ($_POST['Sonne'] == "False" || $_POST['Sonne'] == "false") {
                    echo "Jetzt speichern!";
                    $rules['sonne']['ein'] = "false";
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                } else {
                    echo 'ERROR kein gültiger boolscher Ausdruck!';
                }
            }
            if (isset($_POST['SonneRunter'])) {
                if (($timestamp = strtotime($_POST['SonneRunter'])) === false) {
                    echo "ERROR die Zeit hat das falsche Format.";
                } else {
                    echo "Jetzt speichern!";
                    $rules['sonne']['runter'] = date('G:i:s', $timestamp);
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                }
            }
            if (isset($_POST['SonneHoch'])) {
                if (($timestamp = strtotime($_POST['SonneHoch'])) === false) {
                    echo "ERROR die Zeit hat das falsche Format.";
                } else {
                    echo "Jetzt speichern!";
                    $rules['sonne']['hoch'] = date('G:i:s', $timestamp);
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                }
            }
            if (isset($_POST['LuftReduzieren'])) {
                if ($_POST['LuftReduzieren'] == "True" || $_POST['LuftReduzieren'] == "true") {
                    echo "Jetzt speichern!";
                    $rules['luftreduziert'] = "true";
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                } else if ($_POST['LuftReduzieren'] == "False" || $_POST['LuftReduzieren'] == "false") {
                    echo "Jetzt speichern!";
                    $rules['luftreduziert'] = "false";
                    file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
                    file_put_contents($path_to_reloadRegeln, "true");
                } else {
                    echo 'ERROR kein gültiger boolscher Ausdruck!';
                }
            }

            #############################################################################################


            # Überschrift der Seiten
            if ($_GET['page'] == 'start') {
                $headline = 'Haussteuerung';
            }

            if ($_GET['page'] == 'rollaeden') {
                $headline = 'Rolläden';
            }

            if ($_GET['page'] == 'editRules') {
                $headline = 'Regeln hinzufügen';
            }

            if ($_GET['page'] == 'legal') {
                $headline = 'Impressum';
            }

            # Überschrift tatsächlich anzeigen
            echo '<h1>' . $headline . '</h1>';

            ######################################################################################################
            # ************************************************************************************************** #
            ######################################################################################################

            # Hier kommt der Inhalt der Seiten

            # Seite zum Rolläden fahren - unsichtbar nur für aktion
            if ($_GET['page'] == 'fahreshutter') {
                $deviceId = null;
                $floor = null;
                $richtung = null;

                if ($_GET['richtung'] == 'runter') {
                    $richtung = 'CMD_Rolladen_Runter';
                } else if ($_GET['richtung'] == 'hoch') {
                    $richtung = 'CMD_Rolladen_Hoch';
                } else if ($_GET['richtung'] == 'stop') {
                    $richtung = 'CMD_Rolladen_Stop';
                }

                // Find device in loaded rollaeden config
                if (isset($_GET['device']) && isset($rollaeden)) {
                    $deviceName = $_GET['device'];
                    foreach ($rollaeden as $row) {
                        if ($row['name'] == $deviceName) {
                            $deviceId = $row['i2c'] ?? null;
                            $floor = $row['floor'] ?? null;
                            break;
                        }
                    }
                }

                // Fallback to old hard-coded mapping for backward compatibility if i2c not found in config
                if (!$deviceId) {
                    if ($_GET['device'] == 'Küche') {
                        $deviceId = '0x0D';
                        $floor = 'EGN';
                    } else if ($_GET['device'] == 'WC') {
                        $deviceId = '0x0F';
                        $floor = 'EGN';
                    } else if ($_GET['device'] == 'Terrasse') {
                        $deviceId = '0x0b';
                        $floor = 'EGN';
                    } elseif ($_GET['device'] == 'Wohnzimmer') {
                        $deviceId = '0x0C';
                        $floor = 'EGN';
                    }
                }

                // Build the command including floor and i2c address
                // Use escapeshellarg to avoid shell injection
                if ($deviceId && $floor && $richtung) {
                    $command_with_parameter = $path_to_rolladiono . " " . escapeshellarg($floor) . " " . escapeshellarg($deviceId) . " " . escapeshellarg($richtung);
                    # capture stderr as well so we see errors from the script
                    exec($command_with_parameter . ' 2>&1', $output, $retval);
                    if ($retval === 0) {
                        $log->info('Rolladenbefehl ausgeführt', [
                            'command' => $command_with_parameter,
                            'output' => $output,
                            'return_value' => $retval
                        ]);
                    } else {
                        $log->error('Rolladenbefehl fehlgeschlagen', [
                            'command' => $command_with_parameter,
                            'output' => $output,
                            'return_value' => $retval
                        ]);
                    }
                } else {
                    $log->error('Fehlende Parameter für Rolladenbefehl', [
                        'device' => $deviceId,
                        'floor' => $floor,
                        'richtung' => $richtung
                    ]);
                }

                # zurück zur Rolladenseite...
                header('Location: index.php?page=rollaeden');
            }

            # Inhalt von Rolläden
            else if ($_GET['page'] == 'rollaeden') {
                echo '<p>Eine Liste mit Rolläden</p>';

                foreach ($rollaeden as $index => $row) {
                    $name = $row['name'];
                    $phone = $row['pos'];
                    $deviceUrlName = urlencode($name);

                    echo "
                    <div class='card'>
                        <img class='profile-picture' src='img/profile-picture.png'>
                        <b>$name</b><br>
                        $phone

                        <a class='ersterbtn' href='?page=fahreshutter&richtung=hoch&device=$deviceUrlName'>Hoch</a>
                        <a class='ersterbtn' href='?page=fahreshutter&richtung=stop&device=$deviceUrlName'>Stop</a>
                        <a class='ersterbtn' href='?page=fahreshutter&richtung=runter&device=$deviceUrlName'>Runter</a>
                    </div>
                    ";
                }
            } else if ($_GET['page'] == 'contacts') {
                echo "
                    <p>Diese Seite Kann gelöscht werden. Die ist nur noch zum Abschreiben da... <b>Kontakte</b></p>
                ";

                foreach ($rules as $index => $row) {
                    $name = $row['name'];
                    $phone = $row['phone'];

                    echo "
                    <div class='card'>
                        <img class='profile-picture' src='img/profile-picture.png'>
                        <b>$name</b><br>
                        $phone

                        <a class='phonebtn' href='tel:$phone'>Anrufen</a>
                        <a class='deletebtn' href='?page=delete&delete=$index'>Löschen</a>
                    </div>
                    ";
                }

                # Brauche ich wirklich ein Impressum?? 
            } else if ($_GET['page'] == 'legal') {
                echo "
                    Hier kommt das Impressum hin
                ";

                # Hier die Regeln! 
            } else if ($_GET['page'] == 'editRules') {
                $MorgensEarly = $rules['morgens']['early'];
                $MorgensLate = $rules['morgens']['late'];
                $AbendsEarly = $rules['abends']['early'];
                $AbendsLate = $rules['abends']['late'];
                $SonneEin = $rules['sonne']['ein'];
                $SonneRunter = $rules['sonne']['runter'];
                $SonneHoch = $rules['sonne']['hoch'];
                $Luftreduziert = $rules['luftreduziert'];

                echo "$eineVariable";
                echo "$eineAndereVar";
                echo "
                    <div>
                        Auf dieser Seite kannst du die Regeln verwalten
                    </div>

                    <form action='?page=editRules' method='POST'>
                        <label>Zeit Morgens früherstens</label>
                        <input placeholder='00:00:00' name='morningearly' value='" . htmlspecialchars($MorgensEarly) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>
                    
                    <form action='?page=editRules' method='POST'>
                        <label>Zeit Morgens spätestens</label>
                        <input placeholder='00:00:00' name='morninglate' value='" . htmlspecialchars($MorgensLate) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>
                    
                    <form action='?page=editRules' method='POST'>
                        <label>Zeit Abends frühestens</label>
                        <input placeholder='00:00:00' name='eveningearly' value='" . htmlspecialchars($AbendsEarly) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>
                    
                    <form action='?page=editRules' method='POST'>
                        <label>Zeit Abends spätestens</label>
                        <input placeholder='00:00:00' name='eveninglate' value='" . htmlspecialchars($AbendsLate) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>
                    
                    <form action='?page=editRules' method='POST'>
                        <label>Sonnenautomatik</label>
                        <input placeholder='true / false' name='Sonne' value='" . htmlspecialchars($SonneEin) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>

                    <form action='?page=editRules' method='POST'>
                        <label>Sonnenautomatik Runter</label>
                        <input placeholder='00:00:00' name='SonneRunter' value='" . htmlspecialchars($SonneRunter) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>

                    <form action='?page=editRules' method='POST'>
                        <label>Sonnenautomatik Hoch</label>
                        <input placeholder='00:00:00' name='SonneHoch' value='" . htmlspecialchars($SonneHoch) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>

                    <form action='?page=editRules' method='POST'>
                        <label>Lüfter reduzieren</label>
                        <input placeholder='true / false' name='LuftReduzieren' value='" . htmlspecialchars($Luftreduziert) . "'>
                        <button type='Submit'>Absenden</button>
                    </form>
                    
                ";
            } 
            # Startseite
            else { 
                echo '<p>Startseite der Haussteuerunng</p>';
                echo 'Sonnenaufgang: ' . $suntimes['sunrise'] . '<br>';
                echo 'Sonnenuntergang: ' . $suntimes['sunset'] . '<br>';
                echo '<br>';
                echo 'Temperatur Kanal 1: ' . $tempvals['temp1'] . '<br>';
                echo 'Temperatur Kanal 2: ' . $tempvals['temp2'] . '<br>';
            }
            ?>
        </div>
    </div>

    <div class="footer">
        (C) 2022 Harald Fries
    </div>
</body>

</html>
