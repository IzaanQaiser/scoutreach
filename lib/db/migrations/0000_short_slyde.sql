CREATE TABLE `companies` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`domain` text,
	`url` text,
	`stage` text,
	`size_band` text,
	`headcount` integer,
	`location` text,
	`industry` text,
	`description` text,
	`last_funding_date` text,
	`investors` text,
	`source` text NOT NULL,
	`tier` text,
	`status` text DEFAULT 'new' NOT NULL,
	`why_them` text,
	`can_hire_me` integer,
	`raw_json` text,
	`scraped_at` text DEFAULT (current_timestamp) NOT NULL
);
--> statement-breakpoint
CREATE TABLE `company_evidence` (
	`id` text PRIMARY KEY NOT NULL,
	`company_id` text NOT NULL,
	`kind` text NOT NULL,
	`url` text NOT NULL,
	`title` text,
	`snippet` text NOT NULL,
	`retrieved_at` text DEFAULT (current_timestamp) NOT NULL,
	FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE TABLE `contacts` (
	`id` text PRIMARY KEY NOT NULL,
	`company_id` text NOT NULL,
	`provider_id` text,
	`first` text,
	`last` text,
	`title` text,
	`seniority` text,
	`department` text,
	`linkedin` text,
	`tenure_months` integer,
	`email` text,
	`email_status` text DEFAULT 'not_fetched' NOT NULL,
	`email_source` text,
	`rank_score` real,
	`selected` integer DEFAULT false NOT NULL,
	`skip_reason` text,
	`created_at` text DEFAULT (current_timestamp) NOT NULL,
	FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE TABLE `events` (
	`id` text PRIMARY KEY NOT NULL,
	`entity` text NOT NULL,
	`entity_id` text NOT NULL,
	`type` text NOT NULL,
	`payload` text,
	`at` text DEFAULT (current_timestamp) NOT NULL
);
