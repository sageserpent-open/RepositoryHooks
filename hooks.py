# Hooks file for Mercurial repositories.
# This is distributed by bundling it into its own repository; if you want to use it, make a shell repository that contains whatever
# code you are working on as a subrepository, then clone this hooks repository into the shell as a sibling of your own code's subrepository.

# Your code's subrepository's ./hg/hgrc file can then refer to this hook at a location relative to its root - because it is a sibling,
# this will look something like '../RepositoryHooks/hooks.py'. Remember, the ./hg/hgrc file to configure is the one in your own code's
# subrepository, *not* the one in the shell repository nor one in the sibling hooks subrepository.

# This allows a shared, version-controlled set of hooks to be set up in one place; clones of the shell repository automatically pick up a
# reference to the shared repository. It is up to the cloned repository's owner to then enable the hook in their own ./hg/hgrc file, so
# the model is voluntary buy-in rather than enforced policy.

# NOTE: you can also directly embed a clone of this hooks repository as a subrepository within your own code's repository - thereby
# avoiding the use of a shell repository. Again, configure the ./hg/hgrc file in your code's repository.

import re
import itertools
import os.path
import mimetypes

def isBinaryFile(fileContext):
	return mimetypes.guess_type(fileContext.path())[0]	# A lousy, but effective test: if the Mime type isn't defined, it's *probably* a text file.
														# Let's see how well this works out in practice...

def isThirdPartyFile(fileContext):
	return re.search(r"/thirdParty/", fileContext.path(), re.IGNORECASE)
	
sufficesForFileTypesThatRequireLeadingTabs = ["py", "markdown", "md"]

sufficesForFileTypesThatAreAutomaticallyFilledWithWhitespaceMessByTools = ["targets", "sln", "fsproj", "csproj"]

def createDisgustingRegularExpressionHackToWorkaroundNotBeingAbleToSupplyExternalHashingAndComparisonToPythonSet(suffices):
	return r"^{0}$".format("|".join(map(lambda (suffix): re.escape(".{0}".format(suffix)), suffices)))
	
regularExpressionForFileTypesThatRequireLeadingTabs = createDisgustingRegularExpressionHackToWorkaroundNotBeingAbleToSupplyExternalHashingAndComparisonToPythonSet(sufficesForFileTypesThatRequireLeadingTabs)

regularExpressionForFileTypesThatAreAutomaticallyFilledWithWhitespaceMessByTools = createDisgustingRegularExpressionHackToWorkaroundNotBeingAbleToSupplyExternalHashingAndComparisonToPythonSet(sufficesForFileTypesThatAreAutomaticallyFilledWithWhitespaceMessByTools)

def isFileOfOneOfASetOfTypes(fileContext, regularExpressionForFileTypes):
	return re.match(regularExpressionForFileTypes, os.path.splitext(fileContext.path())[1], re.IGNORECASE)

def isFileThatRequiresLeadingTabs(fileContext):
	return isFileOfOneOfASetOfTypes(fileContext, regularExpressionForFileTypesThatRequireLeadingTabs)
	
def isFileThatWillBeMessedUpByATool(fileContext):
	return isFileOfOneOfASetOfTypes(fileContext, regularExpressionForFileTypesThatAreAutomaticallyFilledWithWhitespaceMessByTools)

def linesMatchingRegularExpression(fileContext, regularExpression):
	return filter(lambda ((lineNumber, line)): re.search(regularExpression, line), zip(itertools.count(1), fileContext.data().splitlines()))

def linesContainingLeadingTabs(fileContext):
	return [] if isFileThatRequiresLeadingTabs(fileContext) else linesMatchingRegularExpression(fileContext, r"^\s*\t\s*\S")

def linesContainingTrailingWhitespace(fileContext):
	return linesMatchingRegularExpression(fileContext, r"\S\s+$")

def whitespaceOnlyLines(fileContext):
	return linesMatchingRegularExpression(fileContext, r"^\s+$")

def preTxnCommitHook(ui, repo, node, **kwargs):
	"""
	In .hg/hgrc, place:
	[hooks]
	pretxncommit = python:<relative directory path from repository root to this file you are reading>/hooks.py:preTxnCommitHook
	"""
	changeContext = repo[node]	# NOTE: don't use 'None' instead of 'node' - this will give us the change context for the working directory,
								# which may be a superset of the changed files in the commit, i.e. some of the file changes were left out
								# of the commit by the user.

	filesExistingInThisCommit = set([fileName for fileName in changeContext])

	fileContexts = [changeContext[fileName] for fileName in changeContext.files() if fileName in filesExistingInThisCommit]	# NOTE: use 'changeContext.files()' rather than 'changeContext' - we only want the files changed
																															# in the commit itself. It would not be fair to punish the latest committer for the sins of previous ones!																															

	relevantFileContexts = [fileContext for fileContext in fileContexts if not (isThirdPartyFile(fileContext) or isBinaryFile(fileContext) or isFileThatWillBeMessedUpByATool(fileContext))]
	
	fileContextsContainingLeadingTabs = list(itertools.ifilter(linesContainingLeadingTabs, relevantFileContexts))
	fileContextsContainingTrailingWhitespace = list(itertools.ifilter(linesContainingTrailingWhitespace, relevantFileContexts))
	fileContextsContainingWhitespaceOnlyLines = list(itertools.ifilter(whitespaceOnlyLines, relevantFileContexts))

	if fileContextsContainingLeadingTabs or fileContextsContainingTrailingWhitespace or fileContextsContainingWhitespaceOnlyLines:
		if fileContextsContainingLeadingTabs:
			ui.warn("Files found containing leading tabs...\n\n")
			for fileContext in fileContextsContainingLeadingTabs:
				ui.warn("\t{0}\n\n".format(fileContext.path()))
				for lineNumber, line in linesContainingLeadingTabs(fileContext):
					ui.warn("\tLine #{0}:{1}\n".format(lineNumber, line))

		if fileContextsContainingLeadingTabs and fileContextsContainingTrailingWhitespace:
			ui.warn("\n")

		if fileContextsContainingTrailingWhitespace:
			ui.warn("Files found containing trailing whitespace...\n\n")
			for fileContext in fileContextsContainingTrailingWhitespace:
				ui.warn("\t{0}\n\n".format(fileContext.path()))
				for lineNumber, line in linesContainingTrailingWhitespace(fileContext):
					ui.warn("\tLine #{0}:{1}\n".format(lineNumber, line))

		if (fileContextsContainingLeadingTabs or fileContextsContainingTrailingWhitespace) and fileContextsContainingWhitespaceOnlyLines:
			ui.warn("\n")

		if fileContextsContainingWhitespaceOnlyLines:
			ui.warn("Files found containing whitespace-only lines...\n\n")
			for fileContext in fileContextsContainingWhitespaceOnlyLines:
				ui.warn("\t{0}\n\n".format(fileContext.path()))
				for lineNumber, line in whitespaceOnlyLines(fileContext):
					ui.warn("\tLine #{0}:{1}\n".format(lineNumber, line))

		return True

	return False