#https://github.com/JunusErgin/php-kontaktbuch/tree/6bfee1b36af1daf4229a1a10dc73f2c93d33a45b
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
            <div class="avatar">8</div>Brentanoweg
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
            $path_to_regeln = "/home/harald/regeln.json";


            # fülle die Hardware
            $newLufter1 = [
                'name' => 'Küche',
                'stufe' => '1'
            ];
            array_push($luefter, $newLufter1);

            $newLufter2 = [
                'name' => 'WC',
                'stufe' => '2'
            ];
            array_push($luefter, $newLufter2);

            $newshutter1 = [
                'name' => 'Küche',
                'pos' => '1'
            ];
            array_push($rollaeden, $newshutter1);

            $newshutter2 = [
                'name' => 'WC',
                'pos' => '0'
            ];
            array_push($rollaeden, $newshutter2);


            # lade Regeln aus Datei
            if (file_exists($path_to_regeln)) {
                $text = file_get_contents($path_to_regeln, true);
                $rules = json_decode($text, true);
            }

            # Speichere neue Regeln falls nötig
            if (isset($_POST['name']) && isset($_POST['phone'])) {
                echo 'Kontakt <b>' . $_POST['name'] . '</b> wurde hinzugefügt';
                $newContact = [
                    'name' => $_POST['name'],
                    'phone' => $_POST['phone']
                ];
                array_push($rules, $newContact);
                file_put_contents($path_to_regeln, json_encode($rules, JSON_PRETTY_PRINT));
            }

            # Überschrift der Seiten
            if ($_GET['page'] == 'start') {
                $headline = 'Ein netter Text';
            }

            if ($_GET['page'] == 'rollaeden') {
                $headline = 'Rolläden';
            }

            if ($_GET['page'] == 'luefter') {
                $headline = 'Lüfter';
            }

            if ($_GET['page'] == 'editRules') {
                $headline = 'Regeln hinzufügen';
            }

            if ($_GET['page'] == 'legal') {
                $headline = 'Impressum';
            }

            # Überschrift tatsächlich anzeigen
            echo '<h1>' . $headline . '</h1>';

###########################################################################
            # Hier kommt der Inhalt der Seiten
            if ($_GET['page'] == 'delete') 
            {
                echo '<p>Dein Kontakt wurde gelöscht</p>';
                # Wir laden die Nummer der Reihe aus den URL Parametern
                $index = $_GET['delete']; 

                # Wir löschen die Stelle aus dem Array 
                unset($rules[$index]); 

                # Tabelle erneut speichern in Datei contacts.txt
                file_put_contents('contacts.txt', json_encode($rules, JSON_PRETTY_PRINT));
            } 
            # Seite zum rolläden fahren
            if ($_GET['page'] == 'fahreshutter') 
            {
                $richt = $_GET['richtung'];
                echo '<p>' . 'Richtung: ' . $richt . '</p>';
                echo '<p>' . 'device: ' . $_GET['device'] . '</p>';


                header('?page=rollaeden');
            } 
            #Seite zum Lüfter schalten
            if ($_GET['page'] == 'schaltelufter') 
            {
                echo '<p>' . 'Stufe: ' . $_GET['stufe'] . '</p>';
                echo '<p>' . 'device: ' . $_GET['device'] . '</p>';


                header('?page=luefter');
            } 
            # Inhalt von Lüftern
            else if ($_GET['page'] == 'luefter') {
                echo '<p>Eine Liste mit Lüftern</p>';
                
                foreach ($luefter as $index=>$row) {
                    $name = $row['name'];
                    $phone = $row['stufe'];

                    echo "
                    <div class='card'>
                        <img class='profile-picture' src='img/profile-picture.png'>
                        <b>$name</b><br>
                        $phone

                        <a class='ersterbtn' href='?page=schaltelufter&stufe=0&device=$name'>Stufe 0</a>
                        <a class='ersterbtn' href='?page=schaltelufter&stufe=1&device=$name'>Stufe 1</a>
                        <a class='ersterbtn' href='?page=schaltelufter&stufe=2&device=$name'>Stufe 2</a>
                        <a class='ersterbtn' href='?page=schaltelufter&stufe=3&device=$name'>Stufe 3</a>
                    </div>
                    ";
                }

            } 
            # Inhalt von Rolläden
            else if ($_GET['page'] == 'rollaeden') {
                echo '<p>Eine Liste mit Rolläden</p>';
                
                foreach ($rollaeden as $index=>$row) {
                    $name = $row['name'];
                    $phone = $row['pos'];

                    echo "
                    <div class='card'>
                        <img class='profile-picture' src='img/profile-picture.png'>
                        <b>$name</b><br>
                        $phone

                        <a class='ersterbtn' href='?page=fahreshutter&richtung=hoch&device=$name'>Hoch</a>
                        <a class='ersterbtn' href='?page=fahreshutter&richtung=stop&device=$name'>Stop</a>
                        <a class='ersterbtn' href='?page=fahreshutter&richtung=runter&device=$name'>Runter</a>
                    </div>
                    ";
                }

            } 
            else if ($_GET['page'] == 'contacts') {
                echo "
                    <p>Auf dieser Seite hast du einen Überblick über deine <b>Kontakte</b></p>
                ";

                foreach ($rules as $index=>$row) {
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
            } else if ($_GET['page'] == 'legal') {
                echo "
                    Hier kommt das Impressum hin
                ";
            } else if ($_GET['page'] == 'editRules') {
                echo "
                    <div>
                        Auf dieser Seite kannst du die Regeln verwalten
                    </div>
                    <form action='?page=contacts' method='POST'>
                        <div>
                            <a>Zeit Abends</a>
                            <input placeholder='00:00:00' name='morning'>
                        </div>
                        <div>
                            <a>Zeit Abends</a>
                            <input placeholder='00:00:00' name='evening'> 
                        </div>
                        <div>
                            <a>Sonnenautomatik</a>
                            <input placeholder='true / false' name='Sonne'> 
                        </div>
                        <div>
                            <a>Sonnenautomatik Runter</a>
                            <input placeholder='00:00:00' name='SonneRunter'> 
                        </div>
                        <div>
                            <a>Sonnenautomatik och</a>
                            <input placeholder='00:00:00' name='SonneHoch'> 
                        </div>
                        <div>
                            <a>Lüfter reduzieren</a>
                            <input placeholder='true / false' name='LuftReduzieren'> 
                        </div>
                        <button type='Submit'>Absenden</button>
                    </form>
                ";
            } else {
                echo 'Du bist auf der Startseite!';
            }
            ?>
        </div>
    </div>

    <div class="footer">
        (C) 2022 Harald Fries
    </div>
</body>

</html>