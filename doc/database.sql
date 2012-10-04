SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

-- --------------------------------------------------------

--
-- Table structure for table `followers`
--

CREATE TABLE IF NOT EXISTS `followers` (
  `key_id` bigint(64) NOT NULL AUTO_INCREMENT,
  `id` bigint(64) unsigned NOT NULL,
  `count` int(9) NOT NULL,
  `fetch_time` datetime NOT NULL,
  PRIMARY KEY (`key_id`),
  KEY `id` (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 ;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `id` bigint(64) unsigned NOT NULL,
  `screen_name` varchar(15) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(32) COLLATE utf8_unicode_ci DEFAULT NULL,
  `location` varchar(128) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` varchar(512) COLLATE utf8_unicode_ci DEFAULT NULL,
  `profile_image_url` varchar(512) COLLATE utf8_unicode_ci NOT NULL,
  `url` varchar(512) COLLATE utf8_unicode_ci DEFAULT NULL,
  `statuses_count` int(10) unsigned NOT NULL DEFAULT '0',
  `followers_count` int(11) unsigned NOT NULL DEFAULT '0',
  `rank` int(11) unsigned NOT NULL DEFAULT '4294967295',
  `old_rank` int(11) unsigned NOT NULL DEFAULT '4294967295',
  `created_at` datetime NOT NULL,
  `fetch_time` datetime NOT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

