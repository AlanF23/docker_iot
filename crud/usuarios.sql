CREATE TABLE `agenda`.`esps` (`id` varchar(11) NOT NULL,`id_sensor` varchar(12) NOT NULL, `usuario_esp` varchar(100) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

ALTER TABLE `esps`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_sensor` (`id_sensor`);
ALTER TABLE `esps`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

