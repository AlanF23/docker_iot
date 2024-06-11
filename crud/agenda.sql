CREATE DATABASE `agenda` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `agenda`;
CREATE TABLE `agenda`.`contactos` (`id` INT NOT NULL AUTO_INCREMENT , `nombre` VARCHAR(100) NULL , `tel` VARCHAR(50) NULL , `email` VARCHAR(50) NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
CREATE USER 'crud'@'%'  IDENTIFIED BY 'cambiarcambiar';
GRANT SELECT, INSERT, UPDATE, DELETE ON `agenda`.* TO 'crud'@'%';

CREATE DATABASE `dispositivos` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `dispositivos`;
CREATE TABLE `dispositivos`.`esps` (`id` varchar(12) NOT NULL, `usuario_esp` varchar(100) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
CREATE USER 'dispositivos'@'%'  IDENTIFIED BY 'alaniot';
GRANT SELECT, INSERT, UPDATE, DELETE ON `dispositivos`.* TO 'dispositivos'@'%';
ALTER TABLE `esps`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `usuario_esp` (`usuario_esp`);
COMMIT;