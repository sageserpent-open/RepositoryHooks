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

sufficesForFileTypesThatRequireLeadingTabs = ["py", "markdown"]

disgustingRegularExpressionHackToWorkaroundNotBeingAbleToSupplyExternalHashingAndComparisonToPythonSet = r"^{0}$".format("|".join(map(lambda (suffix): re.escape(".{0}".format(suffix)), sufficesForFileTypesThatRequireLeadingTabs)))

def isFileThatRequiresLeadingTabs(fileContext):
	return re.match(disgustingRegularExpressionHackToWorkaroundNotBeingAbleToSupplyExternalHashingAndComparisonToPythonSet, os.path.splitext(fileContext.path())[1], re.IGNORECASE)
	
def linesMatchingRegularExpression(fileContext, regularExpression):
	return filter(lambda ((lineNumber, line)): re.search(regularExpression, line), zip(itertools.count(1), fileContext.data().splitlines()))

def linesContainingLeadingTabs(fileContext):
	return [] if isFileThatRequiresLeadingTabs(fileContext) else linesMatchingRegularExpression(fileContext, r"^\s*\t\s*\S")

def linesContainingTrailingWhitespace(fileContext):
	return linesMatchingRegularExpression(fileContext, r"\S\s+$")
	
def whitespaceOnlyLines(fileContext):
	return linesMatchingRegularExpression(fileContext, r"^\s+$")

def preTxnCommitHook(ui, repo, **kwargs):
	"""
	In .hg/hgrc, place:
	[hooks]
	pretxncommit = python:<relative directory path from repository root to this file you are reading>/hooks.py:preTxnCommitHook
	"""
	changeContext = repo[None]

	fileContexts = [changeContext[fileName] for fileName in changeContext.files()]	# NOTE: use 'changeContext.files()' rather than 'changeContext' - we only want the files changed
																					# in the commit itself. It would not be fair to punish the latest committer for the sins of previous ones!

	relevantFileContexts = list(itertools.ifilterfalse(isThirdPartyFile, fileContexts))

	fileContextsContainingLeadingTabs = list(itertools.ifilter(linesContainingLeadingTabs, relevantFileContexts))
	fileContextsContainingTrailingWhitespace = list(itertools.ifilter(linesContainingTrailingWhitespace, relevantFileContexts))
	fileContextsContainingWhitespaceOnlyLines = list(itertools.ifilter(whitespaceOnlyLines, relevantFileContexts))

	if fileContextsContainingLeadingTabs or fileContextsContainingTrailingWhitespace or fileContextsContainingWhitespaceOnlyLines:
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

		if (fileContextsContainingLeadingTabs or fileContextsContainingTrailingWhitespace) and fileContextsContainingWhitespaceOnlyLines:
			ui.warn("\n")

		if fileContextsContainingWhitespaceOnlyLines:
			ui.warn("Files found containing whitespace-only lines...\n\n")
			for fileContext in fileContextsContainingWhitespaceOnlyLines:
				ui.warn("\t{0}\n".format(fileContext.path()))
				for lineNumber, line in whitespaceOnlyLines(fileContext):
					ui.warn("\tLine #{0}:{1}\n".format(lineNumber, line))

		return True

	return False