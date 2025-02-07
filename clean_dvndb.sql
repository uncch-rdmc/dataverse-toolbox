/* current size of importtest database */
select pg_size_pretty(pg_database_size('importtest'));
/* these entries are useless and consume a ton of storage */
delete from actionlogrecord where useridentifier=':guest';
/* write a clean copy of actionlogrecord to reclaim storage */
vacuum full actionlogrecord;
/* drop old tables from 3 to 4 migration */
drop table _dvn3_coll_studies;
drop table _dvn3_study;
drop table _dvn3_study_usergroup;
drop table _dvn3_study_vdcuser;
drop table _dvn3_studyfile_usergroup;
drop table _dvn3_studyfile_vdcuser;
drop table _dvn3_studyversion;
drop table _dvn3_usergroup;
drop table _dvn3_vdc;
drop table _dvn3_vdc_linked_collections;
drop table _dvn3_vdc_usergroup;
drop table _dvn3_vdccollection;
drop table _dvn3_vdcnetwork;
drop table _dvn3_vdcrole;
drop table _dvn3_vdcuser;
drop table _dvn3_vdcuser_usergroup;
drop table _dvn3_versioncontributor;
/* current size of importtest database */
select pg_size_pretty(pg_database_size('importtest'));
