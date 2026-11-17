import json,tempfile,unittest
from pathlib import Path
from collect_preflight import git,inventory,collect,load_exact,commit

class RealGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.repo=self.root/'repo';self.repo.mkdir()
        git(self.repo,'init','-q','-b','base');git(self.repo,'config','user.name','fixture');git(self.repo,'config','user.email','fixture@example.invalid')
        (self.repo/'shared.txt').write_text('base');git(self.repo,'add','.');git(self.repo,'commit','-qm','base')
        git(self.repo,'switch','-qc','incoming');(self.repo/'shared.txt').write_text('incoming');git(self.repo,'commit','-qam','incoming')
        git(self.repo,'switch','-qc','local','base');(self.repo/'shared.txt').write_text('local');git(self.repo,'commit','-qam','local')
        self.engine=load_exact(Path(__file__).resolve().parent.parent/'original/scripts/parallel_preflight.py')
    def tearDown(self):self.tmp.cleanup()
    def test_actual_trees(self):
        self.assertEqual(len(inventory(self.repo,commit(self.repo,'local'))[0]),1)
        r=collect(self.repo,'local',['incoming'],self.engine,self.root/'out');self.assertFalse(r['merge_authorized']);self.assertEqual(r['results'][0]['manual_count'],1)
        q=json.loads((self.root/'out/01/review.json').read_text());self.assertEqual(q['rows'][0]['status'],'DIVERGED');self.assertEqual(commit(self.repo,'HEAD'),commit(self.repo,'local'))
    def test_duplicate_ref(self):self.assertRaisesRegex(ValueError,'REF_SET',collect,self.repo,'local',['incoming','incoming'],self.engine,self.root/'out')
    def test_existing_output(self):
        (self.root/'out').mkdir();self.assertRaises(FileExistsError,collect,self.repo,'local',['incoming'],self.engine,self.root/'out')
    def test_mode_symlink_hold(self):
        (self.repo/'link').symlink_to('shared.txt');git(self.repo,'add','link');git(self.repo,'commit','-qm','link');self.assertRaisesRegex(ValueError,'UNSUPPORTED_MODE',inventory,self.repo,commit(self.repo,'HEAD'))

if __name__=='__main__':unittest.main()
