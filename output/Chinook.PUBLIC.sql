use schema "Chinook".public;

create or replace table "Album" (
  "AlbumId" int primary key,
  "Title" varchar(160) not null,
  "ArtistId" int not null
);

create or replace table "Artist" (
  "ArtistId" int primary key,
  "Name" varchar(120)
);

create or replace table "Customer" (
  "CustomerId" int primary key,
  "FirstName" varchar(40) not null,
  "LastName" varchar(20) not null,
  "Company" varchar(80),
  "Address" varchar(70),
  "City" varchar(40),
  "State" varchar(40),
  "Country" varchar(40),
  "PostalCode" varchar(10),
  "Phone" varchar(24),
  "Fax" varchar(24),
  "Email" varchar(60) not null,
  "SupportRepId" int
);

create or replace table "Employee" (
  "EmployeeId" int primary key,
  "LastName" varchar(20) not null,
  "FirstName" varchar(20) not null,
  "Title" varchar(30),
  "ReportsTo" int,
  "BirthDate" timestamp,
  "HireDate" timestamp,
  "Address" varchar(70),
  "City" varchar(40),
  "State" varchar(40),
  "Country" varchar(40),
  "PostalCode" varchar(10),
  "Phone" varchar(24),
  "Fax" varchar(24),
  "Email" varchar(60)
);

create or replace table "Genre" (
  "GenreId" int primary key,
  "Name" varchar(120)
);

create or replace table "Invoice" (
  "InvoiceId" int primary key,
  "CustomerId" int not null,
  "InvoiceDate" timestamp not null,
  "BillingAddress" varchar(70),
  "BillingCity" varchar(40),
  "BillingState" varchar(40),
  "BillingCountry" varchar(40),
  "BillingPostalCode" varchar(10),
  "Total" number(10,2) not null
);

create or replace table "InvoiceLine" (
  "InvoiceLineId" int primary key,
  "InvoiceId" int not null,
  "TrackId" int not null,
  "UnitPrice" number(10,2) not null,
  "Quantity" int not null
);

create or replace table "MediaType" (
  "MediaTypeId" int primary key,
  "Name" varchar(120)
);

create or replace table "Playlist" (
  "PlaylistId" int primary key,
  "Name" varchar(120)
);

create or replace table "PlaylistTrack" (
  "PlaylistId" int not null,
  "TrackId" int not null,
  primary key ("PlaylistId", "TrackId")
);

create or replace table "Track" (
  "TrackId" int primary key,
  "Name" varchar(200) not null,
  "AlbumId" int,
  "MediaTypeId" int not null,
  "GenreId" int,
  "Composer" varchar(220),
  "Milliseconds" int not null,
  "Bytes" int,
  "UnitPrice" number(10,2) not null
);

alter table "Album"
  add foreign key ("ArtistId") references "Artist" ("ArtistId");

alter table "Customer"
  add foreign key ("SupportRepId") references "Employee" ("EmployeeId");

alter table "Employee"
  add foreign key ("ReportsTo") references "Employee" ("EmployeeId");

alter table "Invoice"
  add foreign key ("CustomerId") references "Customer" ("CustomerId");

alter table "InvoiceLine"
  add foreign key ("InvoiceId") references "Invoice" ("InvoiceId");

alter table "InvoiceLine"
  add foreign key ("TrackId") references "Track" ("TrackId");

alter table "PlaylistTrack"
  add foreign key ("PlaylistId") references "Playlist" ("PlaylistId");

alter table "PlaylistTrack"
  add foreign key ("TrackId") references "Track" ("TrackId");

alter table "Track"
  add foreign key ("AlbumId") references "Album" ("AlbumId");

alter table "Track"
  add foreign key ("GenreId") references "Genre" ("GenreId");

alter table "Track"
  add foreign key ("MediaTypeId") references "MediaType" ("MediaTypeId");

