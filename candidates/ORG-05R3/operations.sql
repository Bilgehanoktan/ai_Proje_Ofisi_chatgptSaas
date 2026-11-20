-- Separate SQLite D0 lab only. No migration of existing databases.
PRAGMA foreign_keys=ON;
CREATE TABLE op_team(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,coordinator TEXT NOT NULL,team_digest TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,project),FOREIGN KEY(t,c,e,rev,coordinator) REFERENCES org_binding(t,c,e,rev,seat)) STRICT;
CREATE TABLE op_member(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,seat TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,project,seat),FOREIGN KEY(t,c,e,rev,project) REFERENCES op_team(t,c,e,rev,project),FOREIGN KEY(t,c,e,rev,seat) REFERENCES org_binding(t,c,e,rev,seat)) STRICT;
CREATE TABLE op_entry(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,seq INTEGER NOT NULL CHECK(seq>0),plan TEXT NOT NULL,task TEXT NOT NULL,sender TEXT NOT NULL,recipient TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind IN ('delegation','handoff')),role TEXT NOT NULL,previous TEXT NOT NULL,digest TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,project,seq),UNIQUE(t,c,e,rev,project,plan,task,sender,recipient,kind),CHECK(sender<>recipient),FOREIGN KEY(t,c,e,rev,project,sender) REFERENCES op_member(t,c,e,rev,project,seat),FOREIGN KEY(t,c,e,rev,project,recipient) REFERENCES op_member(t,c,e,rev,project,seat),FOREIGN KEY(t,c,e,rev,recipient,role) REFERENCES org_position(t,c,e,rev,id,role)) STRICT;
CREATE TABLE op_notice(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,seq INTEGER NOT NULL,digest TEXT NOT NULL,state TEXT NOT NULL CHECK(state='HOLD'),PRIMARY KEY(t,c,e,rev,project,seq),FOREIGN KEY(t,c,e,rev,project,seq) REFERENCES op_entry(t,c,e,rev,project,seq)) STRICT;
