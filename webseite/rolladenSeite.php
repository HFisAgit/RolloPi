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
    <?php
        echo '<p>Eine Liste mit Rolläden</p>';

        foreach ($rollaeden as $index => $row) {
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
    ?>
</body>