1.1.1 / 2015-11-03
==================
* [Bug] (`befa202 <https://github.com/schematics/schematics/commit/befa202c3b3202aca89fb7ef985bdca06f9da37c>`_) Fix Unicode issue with DecimalType
* [Documentation] (`41157a1 <https://github.com/schematics/schematics/commit/41157a13896bd32a337c5503c04c5e9cc30ba4c7>`_) Documentation overhaul
* [Bug] (`860d717 <https://github.com/schematics/schematics/commit/860d71778421981f284c0612aec665ebf0cfcba2>`_) Fix import that was negatively affecting performance
* [Feature] (`93b554f <https://github.com/schematics/schematics/commit/93b554fd6a4e7b38133c4da5592b1843101792f0>`_) Add DataObject to datastructures.py
* [Bug] (`#236 <https://github.com/schematics/schematics/pull/236>`_) Set `None` on a field that's a compound type should honour that semantics
* [Maintenance] (`#348 <https://github.com/schematics/schematics/pull/348>`_) Update requirements
* [Maintenance] (`#346 <https://github.com/schematics/schematics/pull/346>`_) Combining Requirements
* [Maintenance] (`#342 <https://github.com/schematics/schematics/pull/342>`_) Remove to_primitive() method from compound types
* [Bug] (`#339 <https://github.com/schematics/schematics/pull/339>`_) Basic number validation
* [Bug] (`#336 <https://github.com/schematics/schematics/pull/336>`_)  Don't evaluate serializable when accessed through class
* [Bug] (`#321 <https://github.com/schematics/schematics/pull/321>`_) Do not compile regex
* [Maintenance] (`#319 <https://github.com/schematics/schematics/pull/319>`_) Remove mock from install_requires

1.1.0 / 2015-07-12
==================
* [Feature] (`#303 <https://github.com/schematics/schematics/pull/303>`_) fix ListType, validate_items adds to errors list just field name without...
* [Feature] (`#304 <https://github.com/schematics/schematics/pull/304>`_) Include Partial Data when Raising ModelConversionError
* [Feature] (`#305 <https://github.com/schematics/schematics/pull/305>`_) Updated domain verifications to fit to RFC/working standards
* [Feature] (`#308 <https://github.com/schematics/schematics/pull/308>`_) Grennady ordered validation
* [Feature] (`#309 <https://github.com/schematics/schematics/pull/309>`_) improves date_time_type error message for custom formats
* [Feature] (`#310 <https://github.com/schematics/schematics/pull/310>`_) accept optional 'Z' suffix for UTC date_time_type format
* [Feature] (`#311 <https://github.com/schematics/schematics/pull/311>`_) Remove commented lines from models.py
* [Feature] (`#230 <https://github.com/schematics/schematics/pull/230>`_) Message normalization

1.0.4 / 2015-04-13
==================
* [Example] (`#286 <https://github.com/schematics/schematics/pull/286>`_) Add schematics usage with Django
* [Feature] (`#292 <https://github.com/schematics/schematics/pull/292>`_) increase domain length to 10 for .holiday, .vacations
* [Feature] (`#297 <https://github.com/schematics/schematics/pull/297>`_) Support for fields order in serialized format
* [Feature] (`#300 <https://github.com/schematics/schematics/pull/300>`_) increase domain length to 32

1.0.3 / 2015-03-07
==================
* [Feature] (`#284 <https://github.com/schematics/schematics/pull/284>`_) Add missing requirement for `six`
* [Feature] (`#283 <https://github.com/schematics/schematics/pull/283>`_) Update error msgs to print out invalid values in base.py
* [Feature] (`#281 <https://github.com/schematics/schematics/pull/281>`_) Update Model.__eq__
* [Feature] (`#267 <https://github.com/schematics/schematics/pull/267>`_) Type choices should be list or tuple

1.0.2 / 2015-02-12
==================
* [Bug](`#280 <https://github.com/schematics/schematics/issues/280`_) Fix the circular import issue.

1.0.1 / 2015-02-01
==================
* [Feature] (`#184 <https://github.com/schematics/schematics/issues/184>`_ / `03b2fd9 <https://github.com/schematics/schematics/commit/03b2fd97fb47c00e8d667cc8ea7254cc64d0f0a0>`_) Support for polymorphic model fields
* [Bug] (`#233 <https://github.com/schematics/schematics/pull/233>`_) Set field.owner_model recursively and honor ListType.field.serialize_when_none
* [Bug](`#252 <https://github.com/schematics/schematics/pull/252>`_) Fixed project URL
* [Feature] (`#259 <https://github.com/schematics/schematics/pull/259>`_) Give export loop to serializable when type has one
* [Feature] (`#262 <https://github.com/schematics/schematics/pull/262>`_) Make copies of inherited meta attributes when setting up a Model
* [Documentation] (`#276 <https://github.com/schematics/schematics/pull/276>`_) Improve the documentation of get_mock_object

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


0.9.4 / 2013-12-08
==================

* [Feature] (`#178 <https://github.com/schematics/schematics/pull/178>`_) Added deserialize_from flag to BaseType for alternate field names on import
* [Bug] (`#186 <https://github.com/schematics/schematics/pull/186>`_) Compoundtype support in ListTypes
* [Bug] (`#181 <https://github.com/schematics/schematics/pull/181>`_) Removed that stupid print statement!
* [Feature] (`#182 <https://github.com/schematics/schematics/pull/182>`_) Default roles system
* [Documentation] (`#190 <https://github.com/schematics/schematics/pull/190>`_) Typos
* [Bug] (`#177 <https://github.com/schematics/schematics/pull/177>`_) Removed `__iter__` from ModelMeta
* [Documentation] (`#188 <https://github.com/schematics/schematics/pull/188>`_) Typos


0.9.3 / 2013-10-20
==================

* [Documentation] More improvements
* [Feature] (`#147 <https://github.com/schematics/schematics/pull/147>`_) Complete conversion over to py.test
* [Bug] (`#176 <https://github.com/schematics/schematics/pull/176>`_) Fixed bug preventing clean override of options class
* [Bug] (`#174 <https://github.com/schematics/schematics/pull/174>`_) Python 2.6 support


0.9.2 / 2013-09-13
==================

* [Documentation] New History file!
* [Documentation] Major improvements to documentation
* [Feature] Renamed ``check_value`` to ``validate_range``
* [Feature] Changed ``serialize`` to ``to_native``
* [Bug] (`#155 <https://github.com/schematics/schematics/pull/155>`_) NumberType number range validation bugfix
