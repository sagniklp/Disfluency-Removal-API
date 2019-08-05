<?php
$dest_dir = $_SERVER['DOCUMENT_ROOT'] . '/storage/audio_messages/';
if(!file_exists($dest_dir)) mkdir($dest_dir, 0777);
move_uploaded_file($_FILES['file']['tmp_name'], $dest_dir . uniqid() . ".mp3");