# Hooks for Mercurial repositories.
# This is distributed by bundling it into its own repository, which is in turn added as a subrepository into whatever repository wants to use the hook.
# The parent repository's ./hg/hgrc file can then refer to this hook at a location relative to the root of the parent repository. This allows a shared,
# version-controlled set of hooks to be set up in one place; clones of the parent repositories automatically pick up a reference to the shared repository.
# It is up to the cloned repository's owner to then enable the hook in their own ./hg/hgrc file, so the model is voluntary buy-in rather than enforced policy.

import re
import itertools
import os.path

def isThirdPartyFile(fileContext):
	return re.search(r"/thirdParty/", fileContext.path(), re.IGNORECASE)

def isFileThatRequiresLeadingTabs(fileContext):
	return re.match(r"^\.py$", os.path.splitext(fileContext.path())[1], re.IGNORECASE)

def linesContainingLeadingTabs(fileContext):
	return [] if isFileThatRequiresLeadingTabs(fileContext) else filter(lambda ((lineNumber, line)): re.search(r"^\t+", line), zip(itertools.count(1), fileContext.data().splitlines()))

def linesContainingTrailingWhitespace(fileContext):
	return filter(lambda ((lineNumber, line)): re.search(r"\s+$", line), zip(itertools.count(1), fileContext.data().splitlines()))

def preTxnCommitHook(ui, repo, **kwargs):
	"""
	In .hg/hgrc, place:
	[hooks]
	pretxncommit = python:<relative directory path from repository root to this file you are reading>/hooks.py:preTxnCommitHook
	"""
	changeContext = repo[None]

	fileContexts = [changeContext[fileName] for fileName in changeContext]

	relevantFileContexts = list(itertools.ifilterfalse(isThirdPartyFile, fileContexts))

	fileContextsContainingLeadingTabs = list(itertools.ifilter(linesContainingLeadingTabs, relevantFileContexts))
	fileContextsContainingTrailingWhitespace = list(itertools.ifilter(linesContainingTrailingWhitespace, relevantFileContexts))

	if fileContextsContainingLeadingTabs or fileContextsContainingTrailingWhitespace:
		if fileContextsContainingLeadingTabs:
			ui.warn("Files found containing leading tabs...\n\n")
			for fileContext in fileContextsContainingLeadingTabs:
				ui.warn("\t{0}\n".format(fileContext.path()))
				for lineNumber, line in linesContainingLeadingTabs(fileContext):
					ui.warn("\tLine #{0}:{1}\n".format(lineNumber, line))

		if fileContextsContainingLeadingTabs and fileContextsContainingTrailingWhitespace:
			ui.warn("\n")

		if fileContextsContainingTrailingWhitespace:
			ui.warn("Files found containing trailing whitespace...\n\n")
			for fileContext in fileContextsContainingTrailingWhitespace:
				ui.warn("\t{0}\n".format(fileContext.path()))
				for lineNumber, line in linesContainingTrailingWhitespace(fileContext):
					ui.warn("\tLine #{0}:{1}\n".format(lineNumber, line))

		return True

	return False