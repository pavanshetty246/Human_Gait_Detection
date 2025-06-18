-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 11, 2024 at 11:06 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `gait`
--

-- --------------------------------------------------------

--
-- Table structure for table `logs`
--

CREATE TABLE `logs` (
  `id` int(11) NOT NULL,
  `physiotherapist_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `filepath` text NOT NULL,
  `result` text NOT NULL,
  `date` datetime(6) NOT NULL DEFAULT current_timestamp(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `logs`
--

INSERT INTO `logs` (`id`, `physiotherapist_id`, `patient_id`, `filepath`, `result`, `date`) VALUES
(1, 1, 1, 'static\\uploads\\Antalgic_Gait.mp4', 'Gait analysis result', '2024-12-04 04:34:18.390349'),
(2, 1, 1, 'static\\uploads\\Antalgic_Gait.mp4', 'Gait analysis result', '2024-12-04 04:34:18.390349'),
(3, 2, 4, 'static\\uploads\\Parkinsonian_Gait_1.mp4', 'Gait analysis result', '2024-12-04 04:34:18.390349'),
(4, 2, 7, 'static\\uploads\\Parkinsonian_Gait_1.mp4', 'Gait analysis result', '2024-12-04 04:34:18.390349'),
(5, 2, 7, 'static\\uploads\\Parkinsonian_Gait_1.mp4', '\n	- Circumduction: 99.07%', '2024-12-04 04:34:18.390349'),
(6, 2, 7, 'static\\uploads\\Parkinsonian_Gait_1.mp4', '\n	- Circumduction: 99.07%', '2024-12-11 15:27:33.398342');

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `age` int(255) NOT NULL,
  `diagnosis` text NOT NULL,
  `physiotherapist_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`id`, `name`, `age`, `diagnosis`, `physiotherapist_id`) VALUES
(1, 'ragu', 34, 'parkinson', 1),
(7, 'Nagendra', 34, 'parkinson', 2);

-- --------------------------------------------------------

--
-- Table structure for table `physiotherapists`
--

CREATE TABLE `physiotherapists` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `email` text NOT NULL,
  `password` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `physiotherapists`
--

INSERT INTO `physiotherapists` (`id`, `name`, `email`, `password`) VALUES
(1, 'Zamiya mariyamma', 'zamiashafi30@gmail.com', '$2b$12$UUClGJpkK.sdL.MUzoP.q.7J9V4SesKbnH2/J0QMb9D7PRTCdoOaa'),
(2, 'Test test', 'test@gmail.com', '$2b$12$GSIqQOcXx2uXzfHfKPJSd.4H1r0.zJe8cP7D/tehzZTiojM7796ZO');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `logs`
--
ALTER TABLE `logs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `physiotherapists`
--
ALTER TABLE `physiotherapists`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `logs`
--
ALTER TABLE `logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `physiotherapists`
--
ALTER TABLE `physiotherapists`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
