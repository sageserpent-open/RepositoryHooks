RepositoryHooks
===============

Hooks for repositories.

Currently, just for Mercurial repositories (although the public repository is on GitHub and welcomes use by Git clients - that's why it's there - I do my day to day work using Mercurial and interoperate using 'hg-git').

I probably will port these to side-by-side Git hooks as well, please be patient ... or better still, fork this and do the port yourself; help is very welcome.

The idea is for this repository to be shared as a subrepository / submodule, depending on whether you use Mercurial or Git. That way you can have a localised set of hooks for your own repository but share changes to the hooks with everyone else, as well as re-use the hooks across several projects.

Note that just setting up a subreposity / submodule is not enough - you still have to tweak your local configuration to enable the hooks.

This is probably a good thing, because most people don't want these hooks to be enabled by default.

Usage
-----

For Mercurial, I recommend following the advice on the Mercurial wiki about subrepository use and use the 'shell' approach.

This means cloning (or setting up from scratch) your own repository - the one you want to apply the hooks to - as a subrepository *inside* a trivial shell repository that does nothing other than collect together subrepositories.

Then place a clone of the 'RepositoryHooks' repository as a subrepository inside the same shell repository.

Then edit the .hg/hgrc configuration file *inside your subrepository for your project* - **not the one directly inside the shell repository**.

Each hook should have a template to cut, paste and tailor into that .hg/hgrc file for each hook.

As an example, I work with a shell repository like this:-

	HGShellRepository/
						.hgsub				(This configures the subrepositories.)
						.hgsubstate

						RepositoryHooks/	(This is a clone of this repository you are reading about as a subrepository.)
						
						NTestCaseBuilder/	(This is the repository I want the hooks to apply to, it is cloned from GitHub as a subrepository.)
											.hg/
												hgrc	(Where I refer to the hooks.)
					
I have an '.hgsub' file like this:-

repositoryhooks = git+ssh://git@github.com:sageserpent-open/RepositoryHooks.git
ntestcasebuilder = git+ssh://git@github.com:sageserpent-open/NTestCaseBuilder.git

My hgrc file *within 'NTestCaseBuilder'* has an entry like this:-


[hooks]
pretxncommit = python:../RepositoryHooks/hooks.py:preTxnCommitHook
			
**NOTE:** the use of the relative path to step up and across into the sibling 'RepositoryHooks' subrepository.

Now you're ready to be hooked. **However**, bear in mind that the hooks apply when you commit in the subrepository for your project - *not the shell repository*.