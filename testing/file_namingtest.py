import config
import sys, unittest
sys.path.insert(0, "../")
from duplicity import dup_time, file_naming, log, globals

config.setup()

class Test36(unittest.TestCase):
	def test_base36(self):
		"""Test conversion to/from base 36"""
		numlist = [0, 1, 10, 1313, 34233, 872338, 2342889,
				   134242234, 1204684368, 34972382455]
		for n in numlist:
			b = file_naming.to_base36(n)
			assert file_naming.from_base36(b) == n, (b, n)

class FileNamingBase:
	"""Holds file naming test functions, for use in subclasses"""
	def test_basic(self):
		"""Check get/parse cycle"""
		dup_time.setprevtime(10)
		dup_time.setcurtime(20)

		filename = file_naming.get("inc", volume_number = 23)
		log.Log("Inc filename: " + filename, 5)
		pr = file_naming.parse(filename)
		assert pr and pr.type == "inc", pr
		assert pr.start_time == 10
		assert pr.end_time == 20
		assert pr.volume_number == 23

		filename = file_naming.get("full-sig")
		log.Log("Full sig filename: " + filename, 5)
		pr = file_naming.parse(filename)
		assert pr.type == "full-sig"
		assert pr.time == 20

		filename = file_naming.get("new-sig")
		pr = file_naming.parse(filename)
		assert pr.type == "new-sig"
		assert pr.start_time == 10
		assert pr.end_time == 20

	def test_suffix(self):
		"""Test suffix (encrypt/compressed) encoding and generation"""
		filename = file_naming.get("inc", manifest = 1, gzipped = 1)
		pr = file_naming.parse(filename)
		assert pr and pr.compressed == 1
		assert pr.manifest

		filename2 = file_naming.get("full", volume_number = 23, encrypted = 1)
		pr = file_naming.parse(filename2)
		assert pr and pr.encrypted == 1
		assert pr.volume_number == 23

	def test_more(self):
		"""More file_parsing tests"""
		if globals.short_filenames:
			pr = file_naming.parse("dns.h112bi.h14rg0.st.g")
		else:
			pr = file_naming.parse("duplicity-new-signatures.2002-08-18T00:04:30-07:00.to.2002-08-20T00:00:00-07:00.sigtar.gpg")
		assert pr, pr
		assert pr.type == "new-sig"
		assert pr.end_time == 1029826800L

		if globals.short_filenames:
			pr = file_naming.parse("dfs.h5dixs.st.g")
			assert pr, pr
			assert pr.type == "full-sig"
			assert pr.time == 1036954144, repr(pr.time)


class FileNamingLong(unittest.TestCase, FileNamingBase):
	"""Test long filename parsing and generation"""
	def setUp(self): globals.short_filenames = 0

class FileNamingShort(unittest.TestCase, FileNamingBase):
	"""Test short filename parsing and generation"""
	def setUp(self): globals.short_filenames = 1


if __name__ == "__main__":
	unittest.main()
