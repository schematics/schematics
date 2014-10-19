1.0.0 / 2014-10-16
==================
* [Documentation] (`#239 <https://github.com/schematics/schematics/issues/239>`_) Fix typo with wording suggestion
* [Documentation] (`#244 <https://github.com/schematics/schematics/issues/244>`_) fix wrong reference in docs
* [Documentation] (`#246 <https://github.com/schematics/schematics/issues/246>`_) Using the correct function name in the docstring
* [Documentation] (`#245 <https://github.com/schematics/schematics/issues/245>`_) Making the docstring match actual parameter names
* [Feature] (`#241 <https://github.com/schematics/schematics/issues/241>`_) Py3k support

0.9.5 / 2014-07-19
==================

* [Feature] (`#191 <https://github.com/schematics/schematics/pull/191>`_) Updated import_data to avoid overwriting existing data. deserialize_mapping can now support partial and nested models.
* [Documentation] (`#192 <https://github.com/schematics/schematics/pull/192>`_) Document the creation of custom types 
* [Feature] (`#193 <https://github.com/schematics/schematics/pull/193>`_) Add primitive types accepting values of any simple or compound primitive JSON type.
* [Bug] (`#194 <https://github.com/schematics/schematics/pull/194>`_) Change standard coerce_key function to unicode
* [Tests] (`#196 <https://github.com/schematics/schematics/pull/196>`_) Test fixes and cleanup
* [Feature] (`#197 <https://github.com/schematics/schematics/pull/197>`_) Giving context to serialization
* [Bug] (`#198 <https://github.com/schematics/schematics/pull/198>`_) Fixed typo in variable name in DateTimeType
* [Feature] (`#200 <https://github.com/schematics/schematics/pull/200>`_) Added the option to turn of strict conversion when creating a Model from a dict
* [Feature] (`#212 <https://github.com/schematics/schematics/pull/212>`_) Support exporting ModelType fields with subclassed model instances
* [Feature] (`#214 <https://github.com/schematics/schematics/pull/214>`_) Create mock objects using a class's fields as a template 
* [Bug] (`#215 <https://github.com/schematics/schematics/pull/215>`_) PEP 8 FTW
* [Feature] (`#216 <https://github.com/schematics/schematics/pull/216>`_) Datastructures cleanup
* [Feature] (`#217 <https://github.com/schematics/schematics/pull/217>`_) Models cleanup pt 1
* [Feature] (`#218 <https://github.com/schematics/schematics/pull/218>`_) Models cleanup pt 2
* [Feature] (`#219 <https://github.com/schematics/schematics/pull/219>`_) Mongo cleanup
* [Feature] (`#220 <https://github.com/schematics/schematics/pull/220>`_) Temporal cleanup
* [Feature] (`#221 <https://github.com/schematics/schematics/pull/221>`_) Base cleanup
* [Feature] (`#224 <https://github.com/schematics/schematics/pull/224>`_) Exceptions cleanup
* [Feature] (`#225 <https://github.com/schematics/schematics/pull/225>`_) Validate cleanup
* [Feature] (`#226 <https://github.com/schematics/schematics/pull/226>`_) Serializable cleanup
* [Feature] (`#227 <https://github.com/schematics/schematics/pull/227>`_) Transforms cleanup
* [Feature] (`#228 <https://github.com/schematics/schematics/pull/228>`_) Compound cleanup
* [Feature] (`#229 <https://github.com/schematics/schematics/pull/229>`_) UUID cleanup
* [Feature] (`#230 <https://github.com/schematics/schematics/pull/231>`_) Booleans as numbers


0.9.4 / 2013-12/08
==================

* [Feature] (`#178 <https://github.com/schematics/schematics/pull/178>`_) Added deserialize_from flag to BaseType for alternate field names on import
* [Bug] (`#186 <https://github.com/schematics/schematics/pull/186>`_) Compoundtype support in ListTypes
* [Bug] (`#181 <https://github.com/schematics/schematics/pull/181>`_) Removed that stupid print statement!
* [Feature] (`#182 <https://github.com/schematics/schematics/pull/182>`_) Default roles system
* [Documentation] (`#190 <https://github.com/schematics/schematics/pull/190>`_) Typos
* [Bug] (`#177 <https://github.com/schematics/schematics/pull/177>`_) Removed `__iter__` from ModelMeta
* [Documentation] (`#188 <https://github.com/schematics/schematics/pull/188>`_) Typos


0.9.3 / 2013-10/20
==================

* [Documentation] More improvements
* [Feature] (`#147 <https://github.com/schematics/schematics/pull/147>`_) Complete conversion over to py.test
* [Bug] (`#176 <https://github.com/schematics/schematics/pull/176>`_) Fixed bug preventing clean override of options class
* [Bug] (`#174 <https://github.com/schematics/schematics/pull/174>`_) Python 2.6 support


0.9.2 / 2013-09/13
==================

* [Documentation] New History file!
* [Documentation] Major improvements to documentation
* [Feature] Renamed ``check_value`` to ``validate_range``
* [Feature] Changed ``serialize`` to ``to_native``
* [Bug] (`#155 <https://github.com/schematics/schematics/pull/155>`_) NumberType number range validation bugfix



